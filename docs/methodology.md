# Technical methodology

## CPTu normalisation

The corrected cone resistance is

\[
q_t=q_c+(1-a)u_2,
\]

where `qc` and `qt` are stored in MPa, `u2` in kPa and `a` is the net area ratio. The implementation therefore divides the pore-pressure correction by 1,000.

With stresses and sleeve friction in kPa:

\[
q_{net}=1000q_t-\sigma_v, \qquad F_r=100f_s/q_{net},
\]

\[
Q_{tn}=\frac{q_{net}}{P_a}\left(\frac{P_a}{\sigma'_v}\right)^n,
\]

\[
I_c=\sqrt{(3.47-\log_{10}Q_{tn})^2+(\log_{10}F_r+1.22)^2},
\]

\[
n=\min\left(1,0.381I_c+0.05\frac{\sigma'_v}{P_a}-0.15\right), \quad P_a=100\ \mathrm{kPa}.
\]

Because `n` and `Ic` depend on each other, the calculation iterates until the change in `Ic` is below `1e-6` or 50 iterations are reached. Physically invalid rows return `NaN` instead of being silently clipped.

## Smoothing and sensitivity

A centred Gaussian filter is applied independently to `qc`, `fs` and `u2`; `qt`, `Qtn`, `Fr` and `Ic` are then recalculated. The workflow compares `sigma = 0.05`, `0.12` and `0.25 m`. The default `0.05 m` was retained because the previous ten-profile assessment reduced first-difference variability by about 72.7% while changing about 6.9% of class assignments.

## Thin layers

Smoothing is an interpretation aid, not proof that short-wavelength signals are noise. Layers thinner than 0.10 m are reported. A defensible optional consolidation rule is limited to thin `A–B–A` sequences, subject to review of sampling interval, pore-pressure response and independent borehole evidence. It is not applied automatically.

## Limitations

- SBTn describes soil behaviour type, not a direct grain-size classification.
- The net area ratio is inferred from published `qc`, `u2` and `qt` when possible; otherwise 0.80 is assumed and reported.
- Thin layers and sharp interfaces may be real and can be attenuated by any smoother.
- Published values are rounded, so exact numerical reproduction is not expected.

## References

1. Oberhollenzer, S. et al. (2021). *Cone penetration test dataset Premstaller Geotechnik*. Data in Brief, 34, 106618. https://doi.org/10.1016/j.dib.2020.106618
2. Robertson, P. K. (2009). Interpretation of cone penetration tests — a unified approach. *Canadian Geotechnical Journal*, 46(11), 1337–1355.
3. Ganju, E. et al. (2017). Automated stratigraphic profiling using cone penetration test data. *Computers and Geotechnics*, 90, 27–38.
