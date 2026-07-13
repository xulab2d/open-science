**Observation**

In angle-aligned MoTe2/WSe2 at `nu=1`, increasing displacement field is reported to drive consecutive transitions: frustrated Mott insulator -> ferromagnetic QAH Mott insulator -> antiferromagnetic valley-coherent Mott state. The first transition occurs without an observed charge-gap closure. Evidence: `claim:promoted_2602_mote2_wse2_consecutive_tpts`; excluded edges note measurement by `observable:compressibility` and `observable:rmCD`.

More generally, an applied layer potential difference can tune band topology, Mott gaps, spin-orbit terms, and effective Dzyaloshinskii-Moriya interactions in twisted TMD moire systems. Evidence: `claim:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interaction_in_twisted_bi`; `paper:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interacti`; `lab_assistant/knowledge/papers/semiconductor_moire_foundations.md`.

**Inference**

Displacement field likely tunes topology by changing the layer-resolved moire potential and hence the Chern character of the relevant bands, while simultaneously modifying interaction-derived magnetic terms. This can reorder competing insulating states: a topologically trivial or frustrated Mott state, a ferromagnetic Chern/QAH Mott state, and an AFM valley-coherent state.

Observable separation, from supplied context:

- QAH: ferromagnetic order plus Chern/topological response; rMCD should detect magnetic/valley polarization, while transport/Hall response would be the expected topology discriminator. Supported indirectly by `claim:promoted_2602_mote2_wse2_consecutive_tpts`.
- AFM valley-coherent: weak or compensated net rMCD compared with ferromagnetic QAH, but signatures of valley coherence would be needed beyond simple charge compressibility. Supported state label: `claim:promoted_2602_mote2_wse2_consecutive_tpts`.
- Frustrated/trivial Mott: insulating/compressibility gap without QAH ferromagnetic Chern signature; first transition lacking charge-gap closure implies topology/order can change without a simple gap-closing feature in compressibility. Evidence: `claim:promoted_2602_mote2_wse2_consecutive_tpts`.
- Optically addressable Chern/spin-valley order in twisted MoTe2 provides an additional diagnostic/control axis: circularly polarized resonant excitation can reverse spin-valley orientation and switch Chern order. Evidence: `claim:promoted_2508_optical_control_chern_order`; `edge:optical_spin_valley_switching_explains_2508_control_claim`.

**Uncertainty**

The supplied context does not give a complete observable table with explicit Hall values, rMCD signs, optical spectra, or compressibility traces for each regime. Therefore, assignments of Hall response to QAH and compensated rMCD to AFM are inference from the phase labels, not directly quoted measurements in the provided context.