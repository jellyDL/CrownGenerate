# Method Figure Assets

The framework generator reads replaceable transparent PNG files from this
directory:

- `scans.png`: registered upper and lower scans shown in static occlusion from a buccal view.
- `margin.png`: the measured margin rendered as a standalone 3D spatial curve.
- `reference_cad.png`: reference CAD crown.
- `reconstructed_mesh.png`: VAE reconstruction.
- `crown_mesh.png`: final generated posterior crown with visible mesh topology.

Images should have a transparent background, no outer frame, and a square
canvas of at least 1200 px. Keep camera orientation and lighting consistent
across the three crown images. Replacing a PNG and rerunning
`generate_method_framework.py` is sufficient; no layout edits are required.

The initial `reconstructed_mesh.png` and `crown_mesh.png` are explicitly
watermarked placeholders rendered from the reference CAD because no trained
model output is available locally. Replace both with genuine model outputs
before submission. The source sample is de-identified at the file level, but
publication still requires confirmation of ethics and data-use authorization.
