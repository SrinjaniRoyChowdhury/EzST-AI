from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
import hashlib

# =========================
# 🔐 CONFIG
# =========================
URI = "neo4j+s://a68cd587.databases.neo4j.io"
USERNAME = "a68cd587"
PASSWORD = "fDC7aO_osuba5n0xtYCy0HbbjGPUrZsNFigaHSPHLsI"

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
model = SentenceTransformer("all-MiniLM-L6-v2")

# =========================
# 🧠 HELPERS
# =========================
def embed(text):
    return model.encode(text).tolist()

def uid(text):
    return hashlib.md5(text.encode()).hexdigest()

# =========================
# 📊 SAMPLE DATA
# =========================
invoices = [
    {
        "invoice_no": "INV-2026-003",
        "seller": {
            "name": "CloudNine Software Services LLP",
            "gst": "29CLDNS7890K1Z4",
            "address": "Bengaluru"
        },
        "buyer": {
            "name": "TechBridge Analytics Pvt Ltd",
            "gst": "33TCHBR2345L1Z6",
            "address": "Chennai"
        },
        "items": [
            {"name": "CRM SaaS Subscription", "qty": 1, "price": 180000},
            {"name": "AWS Hosting", "qty": 1, "price": 96000},
            {"name": "API Integration", "qty": 40, "price": 1500}
        ],
        "summary": "Total 449580 with IGST 18%"
    }
]

# =========================
# 🚀 CORE FUNCTION
# =========================
def insert_graph(tx, inv):

    # --- Invoice Node ---
    tx.run("""
        MERGE (i:Invoice {invoice_no: $inv_no})
        SET i.embedding = $embedding
    """, inv_no=inv["invoice_no"],
         embedding=embed(inv["invoice_no"]))

    # --- Seller ---
    tx.run("""
        MERGE (s:Company {name: $name})
        MERGE (g:GST {number: $gst})
        MERGE (a:Address {text: $addr})

        MERGE (s)-[:HAS_GST]->(g)
        MERGE (s)-[:LOCATED_AT]->(a)
    """, name=inv["seller"]["name"],
         gst=inv["seller"]["gst"],
         addr=inv["seller"]["address"])

    # --- Buyer ---
    tx.run("""
        MERGE (b:Company {name: $name})
        MERGE (g:GST {number: $gst})
        MERGE (a:Address {text: $addr})

        MERGE (b)-[:HAS_GST]->(g)
        MERGE (b)-[:LOCATED_AT]->(a)
    """, name=inv["buyer"]["name"],
         gst=inv["buyer"]["gst"],
         addr=inv["buyer"]["address"])

    # --- Relationships ---
    tx.run("""
        MATCH (s:Company {name: $seller}),
              (b:Company {name: $buyer}),
              (i:Invoice {invoice_no: $inv_no})
        MERGE (s)-[:ISSUED]->(i)
        MERGE (b)-[:RECEIVED]->(i)
    """, seller=inv["seller"]["name"],
         buyer=inv["buyer"]["name"],
         inv_no=inv["invoice_no"])

    # =========================
    # ✂️ CHUNKS
    # =========================

    chunks = []

    # Header chunk
    chunks.append(f"Invoice {inv['invoice_no']} between {inv['seller']['name']} and {inv['buyer']['name']}")

    # Seller chunk
    chunks.append(f"Seller {inv['seller']['name']} GST {inv['seller']['gst']} located at {inv['seller']['address']}")

    # Buyer chunk
    chunks.append(f"Buyer {inv['buyer']['name']} GST {inv['buyer']['gst']} located at {inv['buyer']['address']}")

    # Item chunks
    for item in inv["items"]:
        chunks.append(f"{item['name']} qty {item['qty']} price {item['price']}")

    # Summary chunk
    chunks.append(inv["summary"])

    # --- Insert Chunks ---
    for chunk in chunks:
        cid = uid(chunk)

        tx.run("""
            MERGE (c:InvoiceChunk {id: $cid})
            SET c.text = $text,
                c.embedding = $embedding
        """, cid=cid,
             text=chunk,
             embedding=embed(chunk))

        tx.run("""
            MATCH (i:Invoice {invoice_no: $inv_no}),
                  (c:InvoiceChunk {id: $cid})
            MERGE (i)-[:HAS_CHUNK]->(c)
        """, inv_no=inv["invoice_no"], cid=cid)

    # =========================
    # 📦 ITEMS + RELATIONS
    # =========================
    for item in inv["items"]:
        iid = uid(item["name"])

        tx.run("""
            MERGE (it:Item {id: $id})
            SET it.name = $name,
                it.qty = $qty,
                it.price = $price,
                it.embedding = $embedding
        """, id=iid,
             name=item["name"],
             qty=item["qty"],
             price=item["price"],
             embedding=embed(item["name"]))

        tx.run("""
            MATCH (i:Invoice {invoice_no: $inv_no}),
                  (it:Item {id: $id})
            MERGE (i)-[:HAS_ITEM]->(it)
        """, inv_no=inv["invoice_no"], id=iid)

        # Link item to chunk (semantic grounding)
        tx.run("""
            MATCH (it:Item {id: $id}),
                  (c:InvoiceChunk)
            WHERE c.text CONTAINS $name
            MERGE (it)-[:MENTIONED_IN]->(c)
        """, id=iid, name=item["name"])


# =========================
# ▶️ RUN
# =========================
with driver.session() as session:
    for inv in invoices:
        session.write_transaction(insert_graph, inv)

driver.close()
print("✅ Advanced Graph Inserted!")