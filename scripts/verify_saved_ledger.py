"""Verify delivered signatures and balances without modifying or replaying the ledger.
The bundled public key must be independently authenticated for identity assurance.
Requires cryptography (included in requirements-extension.txt).
"""
from pathlib import Path
import json,sqlite3,hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=ROOT/'results/extension';key=Ed25519PublicKey.from_public_bytes(bytes.fromhex((p/'ledger_public_key.hex').read_text().strip()))
 expected=json.loads((p/'settlement_stream.json').read_text());db=sqlite3.connect((p/'signed_settlements.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
 found={};balances=[1000000000]*6+[0]
 for ident,payload,sig in db.execute('SELECT id,payload,signature FROM ledger'):
  key.verify(sig,payload.encode());r=json.loads(payload)
  assert r['id']==ident and ident not in found
  raw={k:v for k,v in r.items() if k!='id'}
  assert hashlib.sha256(json.dumps(raw,sort_keys=True).encode()).hexdigest()==ident
  assert 0<=r['seller']<6 and 0<=r['buyer']<6 and r['seller']!=r['buyer'] and r['micro_kwh']>0 and r['amount']>0 and r['fee']>=0
  found[ident]=r
 for r in expected:
  assert found[r['id']]==r
  balances[r['buyer']]-=r['amount']+r['fee'];balances[r['seller']]+=r['amount'];balances[6]+=r['fee'];assert min(balances)>=0
 stored=[r[0] for r in db.execute('SELECT amount FROM balances ORDER BY house')];db.close()
 assert len(found)==len(expected)==64 and stored==balances and sum(balances)==6000000000
 assert balances==json.loads((p/'ledger_results.json').read_text())['balances']
 print(json.dumps({'verified_signatures':len(found),'payload_and_identifier_match':True,'reconstructed_balance_parity':True,'total_accounting_units':sum(balances),'scope':'Read-only verification of the delivered database against the delivered public key and stream. Operator identity and meter truth remain external.'},indent=2))
if __name__=='__main__':main()
