**Observation**

Increasing displacement field in angle-aligned `MoTe2/WSe2` at `nu=1` is reported to drive consecutive transitions:
frustrated Mott insulator -> ferromagnetic QAH Mott insulator -> antiferromagnetic valley-coherent Mott state. The first transition occurs without an observed charge-gap closure. Evidence: `claim:promoted_2602_mote2_wse2_consecutive_tpts`.

The supplied graph also says layer potential difference can tune band topology, Mott gaps, spin-orbit terms, and effective Dzyaloshinskii-Moriya interactions in twisted TMD bilayers, specifically twisted bilayer WSe2. Evidence: `claim:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interaction_in_twisted_bi`, `paper:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interacti`, `lab_assistant/knowledge/papers/semiconductor_moire_foundations.md`.

Named observables in the context for the MoTe2/WSe2 transition include compressibility and RMCD, via excluded graph edges `edge:promoted_2602_tpts_measured_by_compressibility` and `edge:promoted_2602_tpts_measured_by_rmcd`.

**Inference**

Displacement field likely tunes topology by changing the layer-resolved moire band structure: it shifts layer energies, modifies Berry curvature/Chern character, and changes exchange/anisotropy terms that select between ferromagnetic valley-polarized, antiferromagnetic, valley-coherent, and topologically trivial Mott states. This inference is supported indirectly by the layer-potential/topology claim in twisted WSe2 and the observed D-field sequence in MoTe2/WSe2.

Observable distinctions, using only context-supported or term-implied logic:

- QAH regime: ferromagnetic Chern/Mott state; should show anomalous Hall response and finite RMCD from spin-valley polarization. Evidence for phase identity: `claim:promoted_2602_mote2_wse2_consecutive_tpts`.
- AFM valley-coherent regime: insulating state with antiferromagnetic order and inter-valley coherence; RMCD should be reduced or sign-compensated compared with ferromagnetic QAH, while compressibility still indicates a Mott gap. Evidence for phase identity and probes: same claim plus RMCD/compressibility edges.
- Valley-coherent regime: distinguished from simple valley-polarized QAH by coherence between valleys rather than net valley polarization; optical/RMCD contrast alone may not fully identify it without phase-sensitive or magnetic-order information. Evidence: `claim:promoted_2602_mote2_wse2_consecutive_tpts`.
- Trivial/frustrated Mott regime: insulating/compressibility gap without QAH topology or robust ferromagnetic RMCD signature; in the cited sequence it precedes the QAH phase at lower displacement field. Evidence: `claim:promoted_2602_mote2_wse2_consecutive_tpts`.

**Uncertainty**

The supplied context does not provide detailed transport signatures, Hall values, hysteresis, Chern numbers, RMCD line shapes, or direct twisted-MoTe2 displacement-field phase diagrams. It supports the MoTe2/WSe2 D-field sequence and names compressibility/RMCD as probes, but it is insufficient to give numeric phase boundaries or a definitive observable table for twisted MoTe2 displacement-field tuning.