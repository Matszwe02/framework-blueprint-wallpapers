# Notice

Framework Blueprint Wallpapers is an **unofficial fan project. It is not affiliated with, sponsored by or endorsed by Framework Computer Inc.**
"Framework" and the Framework gear logo are trademarks of Framework Computer Inc. They appear here only to identify the laptops shown.
The CC BY licence of the CAD data does not grant any trademark rights.

## Framework CAD (CC BY 4.0)

The models, the derived meshes in `*/cad/`, the baked `*/scene.blend` files and the rendered videos and images are adaptations of CAD published by Framework Computer Inc. under the
[Creative Commons Attribution 4.0 International licence](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0). Each repository states: "© Framework Computer Inc, licensed under CC BY 4.0".

| Laptop | Source repository | Files used |
|--------|-------------------|------------|
| Framework Laptop 13 | [FrameworkComputer/Framework-Laptop-13](https://github.com/FrameworkComputer/Framework-Laptop-13) (© 2026) | `Framework Laptop 13 CAD.stp`, `Battery/FWKNAQ9_G01_20210911.stp` |
| Framework Laptop 13 Pro | [FrameworkComputer/Framework-Laptop-13](https://github.com/FrameworkComputer/Framework-Laptop-13) (© 2026) | `Framework Laptop 13 Pro CAD.stp` plus the Laptop 13 files above (cards, battery) |
| Framework Laptop 12 | [FrameworkComputer/Framework-Laptop-12](https://github.com/FrameworkComputer/Framework-Laptop-12) (© 2024) | `Framework Laptop 12 CAD.stp`, `Battery/Framework_Laptop_12_50_Battery.stp`, `Mainboard/FRAMEWORK_LAPTOP_12_MAINBOARD_V01.stp` |
| Framework Laptop 16 | [FrameworkComputer/Framework-Laptop-16](https://github.com/FrameworkComputer/Framework-Laptop-16) (© 2024) | `Framework Laptop 16 with Graphics Module CAD.zip`, `Mainboard/Framework_Laptop_16_Mainboard_3D.stp`, `Hinges/framework_laptop_16_hinge_assy_asm.stp`, plus the Laptop 13 expansion cards |

### Changes made to the original material

- The STEP models were tessellated into triangle meshes, their feature edges were extracted, and parts were grouped, recoloured and re-posed (opened, exploded, animated).
- Expansion cards for the 13 Pro and 16 are copies of the Laptop 13 card models. Duplicate and variant parts were dropped.
- 13 Pro and Laptop 13 mainboards use the community 3D model 'Framework Mainboard v2' (printables.com/model/1058946, `cad/mainboard.step`; not Framework's CAD, licence not verified); its placement is inferred. The Laptop 12 keycaps are generated from the openings in the input cover.
- The Laptop 16 battery is an estimate sized to the free space in the chassis. Framework publishes no 16 battery model.
- Parts, dimensions and labels are therefore **approximations, not official drawings**.

Framework does not endorse these adaptations; the licensor's name is used only to give the attribution CC BY requires.

## Fonts (SIL Open Font License 1.1)

- Rajdhani, © 2014 Indian Type Foundry: `fonts/OFL-rajdhani.txt`
- Share Tech Mono, © 2012 Carrois Type Design: `fonts/OFL-sharetechmono.txt`

## Code

The code and configuration are MIT-licensed, see `LICENSE`. Dependencies (numpy, Pillow, SciPy, skia-python) and Blender (GPL) keep their own licences.
