# Lab Storage Layout

Refreshed: 2026-07-07 from shallow NAS inspection and user guidance.

Purpose:
- Capture how Xu Lab files are organized in practice.
- Help future searches start in the right layer: personal assembly/provenance folders, shared measurement roots, instrument roots, or summary roots.

## General Model

The NAS root is `/Volumes/Xu Lab`.

Most current lab members have a top-level personal folder. These folders are often the best place to find:
- flake and optical microscope pictures
- AFM characterization and cleaning/cutting records
- transfer and device-assembly process records
- EBL/KLayout/GDS designs
- backgate/topgate/contact-gate design records
- personal notes, talks, posters, and draft summaries
- occasional measurements and local analysis scripts

Shared scientific folders usually hold the more complete measurement campaigns, data, local acquisition/analysis scripts, and project decks. For current tMoTe2 optical/magnetic work, the primary shared root is:
- `/Volumes/Xu Lab/tMoTe2_Measuring`

Operational rule:
- For project science or final measurement interpretation, start from the shared project root.
- For fabrication history, device provenance, flake selection, AFM, EBL design, or assembly context, start from the responsible person's personal folder.
- If a shared project folder is ambiguous, use personal folders to recover device lineage and then jump back to the shared measurement root.

Do not infer current lab membership from folder presence alone. Use `context/people.md` for current roster truth.

## Current-Member Personal Folders

### Xiaodong Xu

No obvious top-level personal folder matched by name in the 2026-07-07 shallow scan.

Related group/PI-facing roots:
- `/Volumes/Xu Lab/Xu Group Meeting`
- `/Volumes/Xu Lab/Group`
- `/Volumes/Xu Lab/Xu Lab equipment inventory`

### Weijie Li

Personal/fabrication root observed:
- `/Volumes/Xu Lab/Weijie_AFM`

Observed structure:
- `Backgate`, `Sample`, `PtSe2`, `KPFM`, `hBN`, `OpticaldeviceAFM`, `Testing`
- contains AFM `.spm`/`.hs*` records, sample images, KPFM/AFM slides, and sample/backgate folders

Shared-project relation:
- Weijie appears in many tMoTe2 project roots as `WJL` or `Weijie`, especially A5, A13, A18, B79, C7, MT48, and D25-related roots.

### Shuai Yuan

Personal root:
- `/Volumes/Xu Lab/Shuai Yuan`

Observed structure:
- `Transfer Stage`, `AFM`, `Fab - 02 - SS`, `Fab - 01 - Graphene-Test`, `EBL`
- transfer-stage decks, backgate/stack summaries, AFM folders, EBL helpers/designs

Shared-project relation:
- Transport/optical tMoTe2 work appears under `/Volumes/Xu Lab/tMoTe2_Measuring`, including MT43 and MT48 roots.

### Yifan Zhao

Personal roots:
- `/Volumes/Xu Lab/Yi-Fan`
- `/Volumes/Xu Lab/Yifan HQ`

Observed structure:
- `AFM`, `SEM`, `Transfer`, `Device`, `Flakes`, `Measurement`, `Documents`
- many SEM/GDS design files, backgate transfer decks, AFM records, device folders, and flake records
- `Yifan HQ` contains MoTe2/HQ-related material

Shared-project relation:
- D93 and D105-style tMoTe2 roots link to Yifan/Yi-Fan project work.

### Naiyuan (James) Zhang

Personal root:
- `/Volumes/Xu Lab/James Zhang`

Observed structure:
- `BurkerIconTemp`, `ParkTemp`, `image_MEMCHQ`, `Device`, `Tescan_Design`, `MoTe2`, `TaS2`, `afmCut`
- Bruker/Park AFM records, D-series device folders, GDS/device designs, microscope images, cutting/cleaning process records

Workflow read:
- This is a fabrication/device-provenance folder rather than a final shared measurement archive.

### Yue Sun

Personal root:
- `/Volumes/Xu Lab/Yue`

Observed structure:
- `Programs`, `Data`, `.ipynb_checkpoints`
- Python measurement/control code and local data organization

Shared-project relation:
- Current D88 coil/MCD work is under `/Volumes/Xu Lab/tMoTe2_Measuring/Yue_D88_1+1+1_AAA_4deg_Attodry522_coilmeasurement`.

### Courtney Baier

Personal root:
- `/Volumes/Xu Lab/Courtney Baier`

Observed structure:
- `hBN`, `MoTe2_transfer`, `Icon`, `Lithography_files`, `WSe2`, `WS2`, `Matlab Code`, `Crystal`, `XuBluefors`
- many microscope images, AFM/Icon records, lithography `.GDS` files, transfer/device folders, and group-meeting decks

Shared-project relation:
- D88, D88 run2, D135, D21, and related tMoTe2 shared roots carry measurement-facing project data.

### Jack Barlow

Personal root:
- `/Volumes/Xu Lab/Jack B`

Observed structure:
- `microscope pictures & afm`, `talks, posters, etc`, `Klayout`, `programs`, `data`, `papers`, `SOPs and manuals`
- microscopy/AFM records, KLayout/GDS design folders, data-analysis programs, talks/posters, SOPs/manuals

Workflow read:
- Broad personal archive spanning device/design work, analysis code, talks, papers, and methods.

### Mai Nguyen

Personal root:
- `/Volumes/Xu Lab/Mai`

Observed structure:
- `Matlab`, `Manuals`, `Device`, `Writing`, `Poster`, `Papers`, `VectorMagnet`, `NanoScopeAnalysis`, CrSBr/CuxTiSe2/PtSe2/HfTe2 folders
- Opticool/birefringence/RMCD-style MATLAB control and analysis scripts, manuals, `.spe` spectroscopy data, sample image folders, and writing materials

Shared-project relation:
- Mai's personal folder is likely the first stop for CrSBr/CuxTiSe2/MnTe-style control scripts and local spectroscopy context before moving into shared instrument or project folders.

### Sinabu Pumulo (Ren)

Personal roots:
- `/Volumes/Xu Lab/Ren P`
- `/Volumes/Xu Lab/ren`

Observed structure:
- `Transferrable Nanobeam Cavity`, `NOISE Lab`, `Alignment Markers`, `Materials`, `CrSBr Disk`, `Code`, `Cleaning`, `Simulations`, MoS2/WSe2-WS2/CrSBr folders
- nanobeam/cavity projects, material folders, PL/SHG files, simulations, alignment markers, cleaning/process records

Workflow read:
- Use both roots when searching Ren's work; one appears to hold broader project/process folders and one has measurement/simulation-style optical data.

### Essance Ray

Personal root:
- `/Volumes/Xu Lab/Essance`

Observed structure:
- `UW U100 STEM Data`, `AFM`, `Xu Lab Data`, `Vienna Data`, `Oak Ridge Data`, `Michigan Cryo Experiments`
- TEM/STEM/EELS-like project folders, AFM folders, collaborator/institution data buckets

Workflow read:
- Personal folder appears centered on microscopy/materials characterization and external-collaboration data movement.

### Julian Alexander Stewart

Personal root:
- `/Volumes/Xu Lab/Julian`

Observed structure:
- `Devices`, `Measure`, `SHG`, `Matlab`, `Documentation`, `Attodry`, `Exfoliation`, `Presentations`, `Write-ups`
- device folders, measurement folders, Attodry/SHG documentation, MATLAB code, presentations, and notes

Shared-project relation:
- AHS3 measurement-facing roots are under `/Volumes/Xu Lab/tMoTe2_Measuring/Julian_AHS3_Attodry911` and `/Volumes/Xu Lab/tMoTe2_Measuring/Julian_AHS3_ScanningPL`.

### Christiano Wang Beach

Personal root:
- `/Volumes/Xu Lab/Christiano`

Observed structure:
- `GaTe Measuring`, `EBL Templates`, `Olympus Pics`, `Glovebox`, `Xu Lab Tranfers`, `Zeiss`, `Opticool`, `MEMC Transfer`
- GaTe scanning-PL roots, EBL templates/GDS files, microscope images, glovebox material records, transfer records, and instrument-related measurement folders

Shared-project relation:
- Current tMoTe2 shared roots include CWB/D24/D25/D88/D93/D135 and Christiano-WJL folders.

### Zengde She

Personal/fabrication root observed:
- `/Volumes/Xu Lab/Zengde AFM`

Observed structure:
- date-coded folders such as `20260610 bg44 47`, `20260611 cut`, `20260209 bg34 A18 bg27`
- AFM `.spm`/`.hs*`, tiff image exports, cleaning/cutting records, backgate/sample identifiers, and cut-pattern files

Shared-project relation:
- Current A-series tMoTe2 roots in `tMoTe2_Measuring` carry Zengde/Weijie measurement data and project decks.

### Isaac Van Orman

Personal root:
- `/Volumes/Xu Lab/Isaac Van Orman`

Observed structure:
- `Icon`, `NbSe2`, `hBN`, `nbse2_012726`, `device1`
- AFM/Icon files, hBN/NbSe2 flake images, device images, and one GDS file

Workflow read:
- Personal folder has experimental/fabrication records, while assistant/tooling work lives in local OpenScience repos rather than the NAS personal folder.

### Eric Zhang

Personal root:
- `/Volumes/Xu Lab/Eric Zhang`

Observed structure:
- `Tops`, `Middle Layer`, `Devices`, `Bottoms`, `Klayout`, `References`, `Fridge`, `Optics`, `Exfoliation`, `Alignmarkers`
- top/middle/bottom stack folders, BN/tMoTe2 design decks, ANM device folders, KLayout/GDS designs, exfoliation and alignment-marker records

Important distinction:
- `/Volumes/Xu Lab/Eric` also exists but should not be assumed to be Eric Zhang's current summer-undergrad folder.

### Louis

Personal root:
- `/Volumes/Xu Lab/Louis`

Observed structure:
- `hBN`
- `Graphite`
- date/sample-coded subfolders such as `20260622_S1` and `20260619_S2`

Workflow read:
- Current folder looks like summer exfoliation/material-selection support.

### Kyle

Likely current personal root:
- `/Volumes/Xu Lab/Kyle`

Observed structure:
- `MEMC Glovebox Search`, `Strain Samples`, `ANL`, `Exfoliation`, `Icon AFM`, `Device Designs`, `Data`, `Oxides`, `ANL UEM`
- exfoliation, AFM, device designs, strain/sample-prep, ANL-related work

Legacy/historical root also present:
- `/Volumes/Xu Lab/KyleH`

Important distinction:
- `KyleH` contains older FePS3, BaFe2As2, CrI3, and pump-probe style work and should not be assumed to be the current summer Kyle without confirmation.

## Shared Roots And How They Relate

### tMoTe2_Measuring

Root:
- `/Volumes/Xu Lab/tMoTe2_Measuring`

Role:
- Shared measurement/result root for tMoTe2 projects.
- Project folders are usually named by owner initials/names, device/sample ID, geometry/twist, and instrument.
- Typical contents: `Data` or `data` directories, `.mat` measurement files, local MATLAB acquisition/analysis scripts, gate conversion scripts, notebooks, and measurement decks.

Observed active examples:
- `Zengde_Weijie_A5_AAtA_dot_oldattodry`
- `Zengde_Weijie_A13_AABB_oldattodry`
- `Zengde_Weijie_A18_BAAB_oldattodry`
- `Zengde_A22_baab_ScanningPL`
- `Shuai_CWB_MT48_attodry911`
- `Yue_D88_1+1+1_AAA_4deg_Attodry522_coilmeasurement`
- `CWB_D24_ScanningPL`
- `CWB_D25_ScanningPL`
- `courtney_christiano_D88_1+1+1_AAA_4deg_attodry911`
- `courtney_christiano_D135_1+1+1_5deg_helical_attodry911`
- `Julian_AHS3_Attodry911`

Search rule:
- For physics interpretation, project status, or processed measurement context, this shared root generally outranks personal folders.

### Shared Measurement / Capability Roots

Current or recurring non-tMoTe2 roots:
- `/Volumes/Xu Lab/SHG`: SHG measurement data, sample images, and SHG analysis scripts.
- `/Volumes/Xu Lab/MnTe`: Opticool/RMCD/birefringence data and MnTe project decks/scripts.
- `/Volumes/Xu Lab/OptiCool`: instrument-organized pump/probe or spectroscopy datasets, often date/sample-coded with notebooks and `.dat` files.
- `/Volumes/Xu Lab/Data`: broad data bucket, including MoTe2 optics/transport branches.

### Shared Instrument / Equipment / Code Roots

Useful operational roots:
- `/Volumes/Xu Lab/Attodry911backup`
- `/Volumes/Xu Lab/Attodry522backup`
- `/Volumes/Xu Lab/Labview`
- `/Volumes/Xu Lab/Equipment Thumb Drives`
- `/Volumes/Xu Lab/Xu Lab equipment inventory`
- `/Volumes/Xu Lab/Infrastructure and equipment`

Role:
- Instrument manuals, backup control code, setup photos, maintenance records, device drivers, order records, and operational documentation.
- Use for setup, control-code, instrument-troubleshooting, or historical-procedure questions.

### Microscope / AFM Shared Roots

Useful roots:
- `/Volumes/Xu Lab/Xu Lab Microscope Pics`
- `/Volumes/Xu Lab/AFM share`
- `/Volumes/Xu Lab/JYAFM`

Role:
- Older or shared microscope/AFM repositories.
- Current member personal folders often contain newer, owner-specific microscope and AFM records.

### Summary / Presentation Roots

Useful roots:
- `/Volumes/Xu Lab/Xu Group Meeting`
- `/Volumes/Xu Lab/Group`
- `/Volumes/Xu Lab/OpenScience/Summaries/PPT`

Role:
- Group meetings, lab-rule decks, broad summaries, OpenScience-generated summaries, and high-level context.
- Use for story reconstruction, prior PI-facing framing, and presentation conventions.

## Practical Search Workflow

1. Identify task type.
- Project science/result: start in `context/projects/active_projects.md`, then shared project root.
- Fabrication/provenance/device lineage: start in the person's folder.
- Instrument/troubleshooting/control: start in instrument/equipment roots.
- Presentation/storyline: start in group meetings, project decks, and OpenScience summaries.

2. Use shallow structure first.
- Inspect top-level and one-level-down folder names before searching raw files.
- Folder names often encode sample IDs, gates, date, instrument, and process step.

3. Use project roots for measurements.
- Once a device/sample is identified, look for the matching shared measurement root.
- Prefer project-local scripts for calibration, gate conversion, background subtraction, and plotting conventions.

4. Keep provenance layered.
- Personal folder = how the sample/device got made and characterized.
- Shared measurement folder = what was measured and how it was analyzed.
- Group/OpenScience summaries = how the result was explained.
- Instrument roots = how hardware/control workflows were run.

5. Avoid false current-activity inference.
- Personal folders and legacy roots may contain former-member or collaborator records.
- Current membership comes from `context/people.md`, not folder names alone.
