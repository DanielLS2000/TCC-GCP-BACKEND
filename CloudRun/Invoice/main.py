# invoice_generator_function/main.py

import base64
import json
import os

from google.cloud import firestore

PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
FIRESTORE_DATABASE_ID = os.environ.get('FIRESTORE_DATABASE_ID', '(default)')

firestore_db = None
if PROJECT_ID:
    try:
        firestore_db = firestore.Client(project=PROJECT_ID, database=FIRESTORE_DATABASE_ID)
        print(f"Firestore client initialized for project {PROJECT_ID}, database {FIRESTORE_DATABASE_ID}")
    except Exception as e:
        print(f"ERROR: Failed to initialize Firestore client: {e}")

def generate_invoice_from_sale(event, context):
    """
    Cloud Function que armazena uma nota fiscal no Firestore,
    usando dados de nota fiscal pré-gerados na mensagem Pub/Sub.

    Args:
        event (dict): O payload do evento Pub/Sub.
        context (google.cloud.functions.Context): Metadados do evento.
    """
    print(f"Received Pub/Sub event: {event}")

    if not event or 'data' not in event:
        print("No Pub/Sub message data found.")
        return 'No message data', 400

    try:
        message_data_encoded = event['data']
        message_data_decoded = base64.b64decode(message_data_encoded).decode('utf-8')
        sale_event_payload = json.loads(message_data_decoded)

        # NOVO: Acessa o invoice_data diretamente do payload da mensagem
        invoice_data = sale_event_payload.get('invoice_data')
        if not invoice_data:
            print("Missing 'invoice_data' in Pub/Sub message payload.")
            return 'Missing invoice_data', 400

        nf_numero = invoice_data.get('nf_id') # Usando nf_id conforme sua estrutura
        if not nf_numero:
            print("Invoice ID (nf_id) missing in invoice_data.")
            return 'Invoice ID missing', 400

        if not firestore_db:
            print("Firestore client not initialized. Cannot store invoice.")
            return 'Firestore not initialized', 500

        # Armazenar a nota fiscal no Firestore usando o nf_numero como ID do documento
        doc_ref = firestore_db.collection('notas_fiscais').document(nf_numero)
        doc_ref.set(invoice_data)
        
        print(f"Invoice {nf_numero} stored in Firestore.")
        return 'Invoice stored successfully', 200

    except Exception as e:
        print(f"Error processing invoice storage: {e}")
        return f"Error processing request: {e}", 500