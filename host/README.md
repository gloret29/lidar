# Station hôte Python

Réception UDP du nuage de points et visualisation temps réel avec Open3D.

## Installation

```bash
cd host
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Utilisation

### Visualisation temps réel

```bash
lidar-visualize --port 9000
```

### Enregistrement seul (sans viewer)

```bash
lidar-receive --port 9000 --output scan.pcd
```

## Protocole

Voir [docs/architecture.md](../docs/architecture.md#protocole-réseau-udp).

## Dépendances

- Python ≥ 3.10
- Open3D ≥ 0.17
- NumPy
