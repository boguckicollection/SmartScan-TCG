import scanner.dataset_builder as db

def test_label_image(tmp_path, monkeypatch):
    img = tmp_path / 'img.jpg'
    img.write_text('')

    monkeypatch.setattr(db, 'scan_image', lambda p: {'Set': 'Base', 'Number': '1/102'})
    monkeypatch.setattr(db, 'analyze_image', lambda p: {'holo': True, 'reverse': False})

    row = db.label_image(img)
    assert row['card_id'] == 'Base-1/102'
    assert row['holo'] is True
    assert row['reverse'] is False

def test_build_dataset(tmp_path, monkeypatch):
    img1 = tmp_path / 'a.jpg'
    img2 = tmp_path / 'b.png'
    img1.write_text('')
    img2.write_text('')

    monkeypatch.setattr(db, 'scan_image', lambda p: {'Set': 'Set', 'Number': '2'})
    monkeypatch.setattr(db, 'analyze_image', lambda p: {'holo': False, 'reverse': True})

    out_csv = tmp_path / 'out.csv'
    rows = db.build_dataset(tmp_path, out_csv)
    assert len(rows) == 2
    assert out_csv.exists()
    text = out_csv.read_text()
    assert 'image_path,card_id,set,holo,reverse' in text
