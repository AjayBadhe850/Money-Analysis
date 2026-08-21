from datetime import date


def test_transaction_crud_flow(client):
    # Register an admin user
    reg = client.post("/api/auth/register", json={
        "name": "Admin Tester",
        "email": "adm.tester@test.com",
        "password": "Password123!",
        "role": "Admin",
        "company_name": "Tx Test Corp"
    }).json()
    token = reg["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Transaction
    tx_payload = {
        "transaction_date": "2026-08-15",
        "description": "AWS Cloud Services Bill",
        "amount": 12500.50,
        "transaction_type": "EXPENSE",
        "payment_method": "Bank Transfer",
        "reference_number": "REF-AWS-001"
    }
    create_resp = client.post("/api/transactions", json=tx_payload, headers=headers)
    assert create_resp.status_code == 200
    created_tx = create_resp.json()
    assert created_tx["amount"] == 12500.50
    assert created_tx["description"] == "AWS Cloud Services Bill"
    tx_id = created_tx["id"]

    # 2. List Transactions with search filter
    list_resp = client.get(f"/api/transactions?search=AWS", headers=headers)
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] >= 1
    assert any(t["id"] == tx_id for t in list_data["items"])

    # 3. Update Transaction
    update_payload = {
        "description": "AWS Cloud Services Bill (Audited)",
        "amount": 12000.00
    }
    update_resp = client.put(f"/api/transactions/{tx_id}", json=update_payload, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["amount"] == 12000.00
    assert update_resp.json()["description"] == "AWS Cloud Services Bill (Audited)"

    # 4. Delete Transaction
    del_resp = client.delete(f"/api/transactions/{tx_id}", headers=headers)
    assert del_resp.status_code == 200

    # Verify deleted
    verify_resp = client.get(f"/api/transactions?search=Audited", headers=headers)
    assert not any(t["id"] == tx_id for t in verify_resp.json()["items"])
