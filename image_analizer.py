from scanner import image_analyzer
image_analyzer.train_type_classifier("scanner/dataset.csv", "scanner/type_model.pt", epochs=5)
