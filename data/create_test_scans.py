import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path

out_dir = Path(__file__).resolve().parent / "test_scans"
out_dir.mkdir(parents=True, exist_ok=True)

def create_chest_xray():
    """Generates an anatomically accurate synthetic chest radiograph for testing."""
    size = (512, 512)
    # Dark background (air outside body)
    arr = np.full(size, 20, dtype=np.float32)
    y, x = np.ogrid[:size[0], :size[1]]

    # Thorax soft tissue ellipse
    thorax_mask = (((x - 256) / 200)**2 + ((y - 280) / 220)**2) <= 1.0
    arr[thorax_mask] = 90.0

    # Lungs (radiolucent air -> darker)
    # Left lung
    left_lung = (((x - 170) / 75)**2 + ((y - 260) / 140)**2) <= 1.0
    # Right lung
    right_lung = (((x - 342) / 75)**2 + ((y - 260) / 140)**2) <= 1.0
    arr[left_lung] = 45.0
    arr[right_lung] = 45.0

    # Mediastinum & Cardiac silhouette (radiopaque tissue -> brighter)
    heart = (((x - 240) / 70)**2 + ((y - 320) / 80)**2) <= 1.0
    arr[heart] = 160.0

    # Spine column down the center
    spine = (np.abs(x - 256) < 18) & (y > 50) & (y < 460)
    arr[spine] += 50.0

    # Clavicles & Rib arches (subtle bony radiopacity)
    for rib_y in range(160, 420, 35):
        rib = (np.abs(y - rib_y - 0.08 * (x - 256)**2 / 50) < 6) & thorax_mask
        arr[rib] += 40.0

    # Diaphragm dome at base
    diaphragm = (y > (370 - 0.001 * (x - 256)**2)) & thorax_mask
    arr[diaphragm] = np.clip(arr[diaphragm] + 70, 0, 255)

    arr = np.clip(arr, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr).filter(ImageFilter.GaussianBlur(radius=3))
    img.save(out_dir / "chest_xray_test.png")
    print(f"Created {out_dir / 'chest_xray_test.png'}")

def create_brain_mri():
    """Generates an axial T2/FLAIR style brain MRI slice for testing."""
    size = (512, 512)
    arr = np.zeros(size, dtype=np.float32)
    y, x = np.ogrid[:size[0], :size[1]]

    # Cranium / Scalp ellipse
    cranium = (((x - 256) / 190)**2 + ((y - 256) / 220)**2) <= 1.0
    skull_bone = (((x - 256) / 180)**2 + ((y - 256) / 210)**2) <= 1.0
    brain_parenchyma = (((x - 256) / 170)**2 + ((y - 256) / 198)**2) <= 1.0

    arr[cranium] = 140.0      # Scalp soft tissue
    arr[skull_bone] = 30.0    # Bone / Cortical skull (dark on T2)
    arr[brain_parenchyma] = 130.0 # Cerebral gray/white matter

    # Interhemispheric fissure (longitudinal fissure)
    fissure = (np.abs(x - 256) <= 2) & brain_parenchyma
    arr[fissure] = 200.0  # CSF bright on T2

    # Lateral ventricles (butterfly / horn shape)
    left_ventricle = (((x - 232) / 16)**2 + ((y - 240) / 45)**2) <= 1.0
    right_ventricle = (((x - 280) / 16)**2 + ((y - 240) / 45)**2) <= 1.0
    arr[left_ventricle] = 230.0  # CSF bright on T2
    arr[right_ventricle] = 230.0

    # Cortical sulci folds
    np.random.seed(42)
    noise = np.random.normal(0, 8, size=size)
    arr[brain_parenchyma] += noise[brain_parenchyma]

    arr = np.clip(arr, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr).filter(ImageFilter.GaussianBlur(radius=2))
    img.save(out_dir / "brain_mri_test.png")
    print(f"Created {out_dir / 'brain_mri_test.png'}")

if __name__ == "__main__":
    create_chest_xray()
    create_brain_mri()
