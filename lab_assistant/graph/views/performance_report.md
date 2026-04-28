# Fact Graph Performance Report

Purpose:
- Quick usefulness audit after expanding the graph.
- Focus on coverage plus whether representative scientific queries pull up the right nodes near the top.

## Coverage
- Nodes: 602
- Edges: 1068
- Paper nodes: 281
- Claim nodes: 234
- Official Xu publication entries parsed: 212
- Paper nodes with official Xu publication provenance: 213
- Curated paper nodes from `knowledge/papers/`: 79

## Official Topic Coverage
- `graphene_moire`: 22
- `moire_tmote2`: 20
- `other_quantum_materials`: 30
- `semiconductor_moire`: 33
- `strain_and_devices`: 13
- `topological_quantum_materials`: 29
- `valley_exciton_optics`: 72
- `vdw_magnetism`: 69

## Retrieval Benchmarks
- Passed: 8/8

### PASS: fractional Chern optical control
- `Paper` score=42: Optical control of integer and fractional Chern insulators
- `Claim` score=38: optical pumping is now being used as an active control knob for integer and fractional Chern states, not just as a passive probe
- `Paper` score=28: Optical control over topological Chern number in moiré materials
- `Claim` score=25: Optical switching of integer and fractional Chern ferromagnets enables bistate cycling and domain-wall writing in twisted MoTe2.
- `Paper` score=23: Direct magnetic imaging of fractional Chern insulators in twisted MoTe2 with a superconducting sensor

### PASS: second moire band ferromagnetism
- `Claim` score=25: second-band ferromagnetism is independently observed and controlled by density and displacement field
- `Claim` score=25: independent evidence for second-band ferromagnetism tuned by density and displacement field
- `Phenomenon` score=20: second moiré band correlated states
- `Claim` score=20: the second moiré band hosts its own ferromagnetism, field-driven Chern behavior, and unusual magnetotransport
- `Paper` score=17: Observation of ferromagnetic phase in the second moiré band of twisted MoTe2

### PASS: magnetic proximity wse2 cri3
- `Paper` score=42: Valley Manipulation by Optically Tuning the Magnetic Proximity Effect in WSe2/CrI3 Heterostructures
- `Claim` score=42: optical spectroscopy can resolve and tune magnetic proximity effects in WSe2/CrI3
- `Claim` score=27: coupling monolayer WTe2 to CrI3 gaps and reprograms the helical edge through magnetic proximity, producing a very large nonreciprocal current set by the CrI3 magnetic state
- `Paper` score=23: Magnetic proximity and nonreciprocal current switching in a monolayer WTe2 helical edge
- `Mechanism` score=20: magnetic proximity effect

### PASS: gate control bilayer cri3 magnetism
- `Paper` score=35: Electrical control of 2D magnetism in bilayer CrI3
- `Claim` score=33: gate field can switch bilayer CrI3 between competing magnetic states
- `Claim` score=31: a gate field can switch bilayer CrI3 between competing magnetic states rather than only perturbing a fixed order
- `Paper` score=24: Stacking-Dependent Magnetism in Bilayer CrI3
- `Paper` score=18: Giant and nonreciprocal second harmonic generation from layered antiferromagnetism in bilayer CrI3

### PASS: moire exciton optical signatures
- `Claim` score=18: interlayer excitons can be trapped by the moiré potential and inherit strong valley-selective optical signatures
- `Paper` score=14: Optical signatures of -1/3 fractional quantum anomalous Hall state in twisted MoTe2
- `Claim` score=14: moire potentials should be viewed as a programmable excitonic lattice, not only as a perturbation to a uniform exciton
- `Claim` score=13: correlated interlayer exciton insulating behavior can emerge in a moire-coupled semiconductor heterostructure and be resolved optically
- `Claim` score=13: moire excitons are a controlled optical platform whose energies, dynamics, and diffusion are tunable by twist angle, stacking, and external fields

### PASS: edge conduction monolayer wte2
- `Paper` score=41: Edge conduction in monolayer WTe2
- `Claim` score=33: monolayer WTe2 develops an insulating bulk while its edges remain conducting below about `100 K`, consistent with a 2D topological-insulator edge mode
- `Paper` score=29: Magnetic proximity and nonreciprocal current switching in a monolayer WTe2 helical edge
- `Claim` score=29: coupling monolayer WTe2 to CrI3 gaps and reprograms the helical edge through magnetic proximity, producing a very large nonreciprocal current set by the CrI3 magnetic state
- `Paper` score=20: Imaging Quantum Spin Hall Edges in Monolayer WTe2

### PASS: interlayer exciton mose2 wse2
- `Paper` score=29: Observation of Long-Lived Interlayer Excitons in Monolayer MoSe2-WSe2 Heterostructures
- `Claim` score=29: MoSe2/WSe2 heterobilayers support long-lived interlayer excitons with spatially separated carriers
- `Paper` score=28: Correlated interlayer exciton insulator in heterostructures of monolayer WSe2 and moiré WS2/WSe2
- `Claim` score=24: correlated interlayer exciton insulating behavior can emerge in a moire-coupled semiconductor heterostructure and be resolved optically
- `Paper` score=24: Coherent exciton-exciton interactions and exciton dynamics in a MoSe2-WSe2 heterostructure

### PASS: fractional Chern insulator local probe bulk edge
- `Paper` score=69: Local probe of bulk and edge states in a fractional Chern insulator
- `Claim` score=61: local probes can resolve both bulk and edge structure in a fractional Chern insulator rather than relying only on global transport
- `Paper` score=36: Observation of dissipationless fractional Chern insulator
- `Claim` score=36: at least some twisted-MoTe2 devices now reach a dissipationless fractional-Chern-insulator regime rather than only near-quantized transport
- `Claim` score=36: local compressibility plus magneto-optics gives bulk evidence for integer and fractional Chern states

## Interpretation
- Broad paper coverage is useful only if representative science queries pull up the right papers or claim nodes near the top.
- Official-publication ingest mainly improves breadth; the curated paper shelves remain the main source of medium-confidence scientific takeaways.
- Misses usually indicate either a missing curated paper shelf, weak concept links, or overly generic search vocabulary.
