# Retrieval Comparison

Purpose:
- Compare fact-graph paper retrieval against a simpler non-graph lexical paper search over the local knowledge corpus.
- Distinguish raw lookup speed from retrieval usefulness.

## Aggregate
- Benchmark queries: 8
- Baseline paper records: 264
- Graph paper hit@5: 8/8
- Baseline paper hit@5: 8/8
- Graph average first relevant paper rank: 1.50
- Baseline average first relevant paper rank: 1.50
- Graph median lookup time: 11.482 ms
- Baseline median lookup time: 3.377 ms

Interpretation:
- On this local corpus, the graph is not faster in raw milliseconds; its advantage has to come from retrieval quality or richer context.
- The graph and the simpler baseline tie on average paper rank for these queries.

## Per Query
### fractional Chern optical control
- Graph first relevant paper rank: 1
- Baseline first relevant paper rank: 1
- Graph top papers:
  - Optical control of integer and fractional Chern insulators
  - Optical control over topological Chern number in moiré materials
  - Direct magnetic imaging of fractional Chern insulators in twisted MoTe2 with a superconducting sensor
  - Thermodynamic evidence of fractional Chern insulator in moire MoTe2
  - Local probe of bulk and edge states in a fractional Chern insulator
- Baseline top papers:
  - Optical control of integer and fractional Chern insulators
  - Optical control over topological Chern number in moiré materials
  - Direct magnetic imaging of fractional Chern insulators in twisted MoTe2 with a superconducting sensor
  - Local probe of bulk and edge states in a fractional Chern insulator
  - Observation of dissipationless fractional Chern insulator

### second moire band ferromagnetism
- Graph first relevant paper rank: 1
- Baseline first relevant paper rank: 1
- Graph top papers:
  - Observation of ferromagnetic phase in the second moiré band of twisted MoTe2
  - Interplay between topology and correlations in the second moiré band of twisted bilayer MoTe2
  - Ferromagnetism and Topology of the Higher Flat Band in a Fractional Chern Insulator
  - Light induced ferromagnetism in moire superlattices
  - Twist-angle transferable continuum model and second flat Chern band in twisted MoTe2 and WSe2
- Baseline top papers:
  - Interplay between topology and correlations in the second moiré band of twisted bilayer MoTe2
  - Observation of ferromagnetic phase in the second moiré band of twisted MoTe2
  - Ferromagnetism and Topology of the Higher Flat Band in a Fractional Chern Insulator
  - Light induced ferromagnetism in moire superlattices
  - Band topology, Hubbard model, Heisenberg model, and Dzyaloshinskii-Moriya interaction in twisted bilayer WSe2

### magnetic proximity wse2 cri3
- Graph first relevant paper rank: 1
- Baseline first relevant paper rank: 1
- Graph top papers:
  - Valley Manipulation by Optically Tuning the Magnetic Proximity Effect in WSe2/CrI3 Heterostructures
  - Magnetic proximity and nonreciprocal current switching in a monolayer WTe2 helical edge
  - Layer-Resolved Magnetic Proximity Effect in van der Waals Heterostructures
  - Magnetic Control of Valley Pseudospin in Monolayer WSe2
  - Probing the Influence of Dielectric Environment on Excitons in Monolayer WSe2: Insight from High Magnetic Fields
- Baseline top papers:
  - Valley Manipulation by Optically Tuning the Magnetic Proximity Effect in WSe2/CrI3 Heterostructures
  - Magnetic proximity and nonreciprocal current switching in a monolayer WTe2 helical edge
  - Gate-tunable proximity effects in graphene on layered magnetic insulators
  - Layer-Resolved Magnetic Proximity Effect in van der Waals Heterostructures
  - Magnetic Control of Valley Pseudospin in Monolayer WSe2

### gate control bilayer cri3 magnetism
- Graph first relevant paper rank: 1
- Baseline first relevant paper rank: 1
- Graph top papers:
  - Electrical control of 2D magnetism in bilayer CrI3
  - Stacking-Dependent Magnetism in Bilayer CrI3
  - Giant and nonreciprocal second harmonic generation from layered antiferromagnetism in bilayer CrI3
  - Optical control of orbital magnetism in magic-angle twisted bilayer graphene
  - Pressure-controlled interlayer magnetism in atomically thin CrI3
- Baseline top papers:
  - Electrical Control of 2D Magnetism in Bilayer CrI3
  - Optical control of orbital magnetism in magic-angle twisted bilayer graphene
  - Stacking-Dependent Magnetism in Bilayer CrI3
  - Competing correlated states and abundant orbital magnetism in twisted monolayer-bilayer graphene
  - Electrical Tuning of Valley Magnetic Moment via Symmetry Control in Bilayer MoS2

### moire exciton optical signatures
- Graph first relevant paper rank: 5
- Baseline first relevant paper rank: 5
- Graph top papers:
  - Optical signatures of -1/3 fractional quantum anomalous Hall state in twisted MoTe2
  - Nano-optical imaging of the tailored exciton-polariton transport in MoSe2 waveguides
  - Nano-optical imaging of exciton polaritons inside WSe2 waveguides
  - Spin-Layer Locking Effects in Optical Orientation of Exciton Spin in Bilayer WSe2
  - Moire excitons: from programmable quantum emitter arrays to spin-orbit coupled artificial lattices
- Baseline top papers:
  - Nano-optical imaging of exciton polaritons inside WSe2 waveguides
  - Nano-optical imaging of the tailored exciton-polariton transport in MoSe2 waveguides
  - Spin-Layer Locking Effects in Optical Orientation of Exciton Spin in Bilayer WSe2
  - Correlated interlayer exciton insulator in heterostructures of monolayer WSe2 and moiré WS2/WSe2
  - Moire excitons: from programmable quantum emitter arrays to spin-orbit coupled artificial lattices

### edge conduction monolayer wte2
- Graph first relevant paper rank: 1
- Baseline first relevant paper rank: 1
- Graph top papers:
  - Edge conduction in monolayer WTe2
  - Magnetic proximity and nonreciprocal current switching in a monolayer WTe2 helical edge
  - Imaging Quantum Spin Hall Edges in Monolayer WTe2
  - Evidence for equilibrium excitons and exciton condensation in monolayer WTe2
  - Majorana Fermions on Zigzag Edge of Monolayer Transition Metal Dichalcogenides
- Baseline top papers:
  - Edge conduction in monolayer WTe2
  - Magnetic proximity and nonreciprocal current switching in a monolayer WTe2 helical edge
  - Evidence for equilibrium excitons and exciton condensation in monolayer WTe2
  - Imaging Quantum Spin Hall Edges in Monolayer WTe2
  - Majorana Fermions on Zigzag Edge of Monolayer Transition Metal Dichalcogenides

### interlayer exciton mose2 wse2
- Graph first relevant paper rank: 1
- Baseline first relevant paper rank: 1
- Graph top papers:
  - Observation of Long-Lived Interlayer Excitons in Monolayer MoSe2-WSe2 Heterostructures
  - Correlated interlayer exciton insulator in heterostructures of monolayer WSe2 and moiré WS2/WSe2
  - Coherent exciton-exciton interactions and exciton dynamics in a MoSe2-WSe2 heterostructure
  - Signatures of moiré-trapped valley excitons in MoSe2/WSe2 heterobilayers
  - Nanocavity Clock Spectroscopy: Resolving Competing Exciton Dynamics in WSe2/MoSe2 Heterobilayers
- Baseline top papers:
  - Observation of Long-Lived Interlayer Excitons in Monolayer MoSe2-WSe2 Heterostructures
  - Coherent exciton-exciton interactions and exciton dynamics in a MoSe2-WSe2 heterostructure
  - Correlated interlayer exciton insulator in heterostructures of monolayer WSe2 and moiré WS2/WSe2
  - Nanocavity Clock Spectroscopy: Resolving Competing Exciton Dynamics in WSe2/MoSe2 Heterobilayers
  - Excited Rydberg States in MoSe2/WSe2 Heterostructures

### fractional Chern insulator local probe bulk edge
- Graph first relevant paper rank: 1
- Baseline first relevant paper rank: 1
- Graph top papers:
  - Local probe of bulk and edge states in a fractional Chern insulator
  - Observation of dissipationless fractional Chern insulator
  - Thermodynamic evidence of fractional Chern insulator in moire MoTe2
  - Evidence of competing ground states between fractional Chern insulator and antiferromagnetism in moire MoTe2
  - Robust non-Abelian even-denominator fractional Chern insulator in twisted bilayer MoTe2
- Baseline top papers:
  - Local probe of bulk and edge states in a fractional Chern insulator
  - Observation of dissipationless fractional Chern insulator
  - Thermodynamic evidence of fractional Chern insulator in moire MoTe2
  - Ferromagnetism and Topology of the Higher Flat Band in a Fractional Chern Insulator
  - Evidence of competing ground states between fractional Chern insulator and antiferromagnetism in moire MoTe2
