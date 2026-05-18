# RNMT-RAM S36p Supplementary Materials

This repository is prepared for GitHub Pages.

Planned public URL:

```text
https://qiangyijia.github.io/S36p_poster/
```

Contents:

- `index.html` - static webpage for supplementary materials
- `assets/S36p_H439_VMD_plus_distance.mp4` - synchronized VMD and H439 distance movie
- `assets/overview.mp4` - RNMT-RAM overview movie
- `assets/*poster.png` - key distance and PBSA plots
- `qr/S36p_poster_QR.png` - QR code for the GitHub Pages URL
- `qr/S36p_poster_QR.svg` - vector QR code for poster/PPT use

To publish:

```bash
cd /Users/2648471/Documents/S36p_poster
git init
git add .
git commit -m "Add S36p poster supplementary materials"
git branch -M main
git remote add origin https://github.com/QiangYiJia/S36p_poster.git
git push -u origin main
```

Then enable GitHub Pages:

1. Open `https://github.com/QiangYiJia/S36p_poster/settings/pages`
2. Under "Build and deployment", choose "Deploy from a branch".
3. Select `main` and `/root`.
4. Save.

After GitHub Pages is active, the QR code should resolve to:

```text
https://qiangyijia.github.io/S36p_poster/
```
