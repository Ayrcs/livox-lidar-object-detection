# Registre de modèles

Les checkpoints suffisamment petits peuvent être suivis directement dans Git
pour simplifier la réutilisation. Chaque version immuable est un dossier
`name_vMAJOR.MINOR.PATCH` contenant au minimum :

```text
model.pth (ou model.onnx/model.engine)
manifest.yaml
config.yaml
classes.yaml
metrics.json
model_card.md
environment.lock.txt
SHA256SUMS
```

`manifest.yaml` est le contrat lu par le nœud ROS. `SHA256SUMS` couvre chaque
fichier livré. Un moteur TensorRT doit rester accompagné du checkpoint source
et de ses contraintes de GPU/CUDA/TensorRT.
