# Falakus — Research Basis

Literature review for NASA Space Apps 2026. DOIs below were checked against the Crossref API (title, first author and year matched) on 2026-11-15. URLs were checked for an HTTP 200 response. Numbers marked *(approx.)* are from memory of the paper; check them against the abstract before quoting them on stage.

---

## 1. SAR water and flood mapping by backscatter thresholding

**[Martinis2009]** Martinis, S., Twele, A., Voigt, S. (2009). Towards operational near real-time flood detection using a split-based automatic threshold selection approach on TerraSAR-X data. *Natural Hazards and Earth System Sciences* 9, 303–314. https://doi.org/10.5194/nhess-9-303-2009
- The paper splits the scene into tiles and picks the tiles with bimodal (water vs. land) histograms. It derives a global threshold from those tiles automatically, so no manual threshold is needed.
- **Supports:** our automatic threshold on low backscatter. **Limits:** it assumes enough open water in the scene to give a bimodal histogram.

**[Twele2016]** Twele, A., Cao, W., Plank, S., Martinis, S. (2016). Sentinel-1-based flood mapping: a fully automated processing chain. *International Journal of Remote Sensing* 37(13). https://doi.org/10.1080/01431161.2016.1192304
- A fully automated Sentinel-1 chain: thresholding, then fuzzy-logic refinement using elevation (HAND), then region growing. Reported accuracy against reference maps was in the mid-to-high 90s % *(approx.)*.
- **Supports:** "threshold plus auxiliary terrain" is an accepted operational design. **Limits:** it is C-band, VV. Wind roughening and dry sand both produce false positives.

**[Bioresita2018]** Bioresita, F., Puissant, A., Stumpf, A., Malet, J.-P. (2018). A Method for Automatic and Rapid Mapping of Water Surfaces from Sentinel-1 Imagery. *Remote Sensing* 10(2), 217. https://doi.org/10.3390/rs10020217
- Automatic thresholding of Sentinel-1 for surface water, with a fuzzy-logic step that reduces misclassification.
- **Supports:** a single-scene, unsupervised water mask is defensible.

### L-band double-bounce in flooded vegetation

**[Hess1995]** Hess, L.L., Melack, J.M., Filoso, S., Wang, Y. (1995). Delineation of inundated area and vegetation along the Amazon floodplain with the SIR-C synthetic aperture radar. *IEEE TGRS* 33(4), 896–904. https://doi.org/10.1109/36.406675
- Flooded forest returns *high* L-band HH backscatter, from trunk–water double-bounce. Open water returns low backscatter. L-band SAR could therefore map inundation under the canopy.

**[Hess2003]** Hess, L.L., Melack, J.M., Novo, E.M.L.M., Barbosa, C.C.F., Gastil, M. (2003). Dual-season mapping of wetland inundation and vegetation for the central Amazon basin. *Remote Sensing of Environment* 87(4). https://doi.org/10.1016/j.rse.2003.04.001
- JERS-1 L-band mosaics from high- and low-water seasons were used to map wetland extent and flooded vegetation across the central Amazon basin.
- **Supports (both Hess papers):** NISAR L-band can see flooding that optical sensors and C-band miss. **Limits:** a plain "low backscatter = water" threshold labels flooded forest as dry. We need a separate bright-anomaly rule, or we have to state this as a limitation.

> Pierdicca et al. (flooded vegetation, COSMO-SkyMed / multifrequency): **no DOI was verified in this pass. Do not cite it.**

## 2. ML water classification: spatial vs. random cross-validation

**[Roberts2017]** Roberts, D.R., Bahn, V., Ciuti, S., et al. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. *Ecography* 40(8), 913–929. https://doi.org/10.1111/ecog.02881
- With autocorrelated data, random k-fold CV puts near-duplicate neighbours in both train and test. This makes error look optimistically low. The authors recommend block CV (spatial, temporal or group blocks).
- **Supports:** our leave-one-region-out / spatial-block validation. The random-pixel score is kept only as an upper bound.

**[Ploton2020]** Ploton, P., Mortier, F., Réjou-Méchain, M., et al. (2020). Spatial validation reveals poor predictive performance of large-scale ecological mapping models. *Nature Communications* 11, 4540. https://doi.org/10.1038/s41467-020-18321-y
- A biomass map of central Africa looked good under random CV (R² ≈ 0.5). Under spatial CV, predictive skill dropped to near zero *(approx.)*.
- **Supports:** the "why random pixel CV leaks" slide. Our honest number is the spatial-CV number.

## 3. Multitemporal SAR change detection and landslides

**[Bazi2005]** Bazi, Y., Bruzzone, L., Melgani, F. (2005). An unsupervised approach based on the generalized Gaussian model to automatic change detection in multitemporal SAR images. *IEEE TGRS* 43(4). https://doi.org/10.1109/TGRS.2004.842441
- The log-ratio image turns multiplicative speckle into additive noise. The authors model it with generalized Gaussians and set the change threshold automatically.
- **Supports:** our log-ratio (dB difference) change layer.

**[Conradsen2016]** Conradsen, K., Nielsen, A.A., Skriver, H. (2016). Determining the Points of Change in Time Series of Polarimetric SAR Data. *IEEE TGRS* 54(5), 3007–3024. https://doi.org/10.1109/TGRS.2015.2510160
- An omnibus likelihood-ratio test (complex Wishart) asks whether a whole time series is constant. A factorization of the test then locates *when* the change happened, with p-values.
- **Supports:** per-pixel "change vs. noise" significance in a time series. **Limits:** if we use a simpler per-pixel variability / z-score, we should present it as a heuristic inspired by this test, not as the test itself.

**[Mondini2019]** Mondini, A.C., Santangelo, M., Rocchetti, M., et al. (2019). Sentinel-1 SAR Amplitude Imagery for Rapid Landslide Detection. *Remote Sensing* 11(7), 760. https://doi.org/10.3390/rs11070760
- Pre- and post-event Sentinel-1 amplitude change detected landslide areas where clouds blocked optical imagery.

**[Mondini2021]** Mondini, A.C., Guzzetti, F., Chang, K.-T., et al. (2021). Landslide failures detection and mapping using Synthetic Aperture Radar: Past, present and future. *Earth-Science Reviews* 216, 103574. https://doi.org/10.1016/j.earscirev.2021.103574
- A review of amplitude, coherence and polarimetric approaches. It notes that the main limitations are geometric distortion (layover and shadow) on steep slopes.

**[Handwerger2022]** Handwerger, A.L., Huang, M.-H., Jones, S.Y., et al. (2022). Generating landslide density heatmaps for rapid detection using open-access satellite radar data in Google Earth Engine. *NHESS* 22, 753–773. https://doi.org/10.5194/nhess-22-753-2022
- Sentinel-1 backscatter change in GEE produced landslide *density heatmaps*, tested on several real events, rather than individual landslide outlines.
- **Supports:** framing our output as a "where to look" heatmap, not a polygon map.

## 4. InSAR earthquake deformation, L-band coherence, ionosphere

**[Massonnet1993]** Massonnet, D., Rossi, M., Carmona, C., et al. (1993). The displacement field of the Landers earthquake mapped by radar interferometry. *Nature* 364, 138–142. https://doi.org/10.1038/364138a0
- The first InSAR map of a co-seismic displacement field (M7.3 Landers, ERS-1). Each fringe is a half-wavelength (~28 mm at C-band) of line-of-sight change.

**[Rosen2000]** Rosen, P.A., Hensley, S., Joughin, I.R., et al. (2000). Synthetic aperture radar interferometry. *Proceedings of the IEEE* 88(3), 333–382. https://doi.org/10.1109/5.838084
- The standard reference for interferometric phase. One fringe (2π) = λ/2 of line-of-sight displacement. At NISAR L-band (λ ≈ 24 cm) that is ≈ 12 cm per fringe.

**[Zebker1992]** Zebker, H.A., Villasenor, J. (1992). Decorrelation in interferometric radar echoes. *IEEE TGRS* 30(5). https://doi.org/10.1109/36.175330
- Defines the sources of decorrelation: spatial baseline, temporal change and thermal noise. Temporal decorrelation is worst over vegetation.

**[WeiSandwell2010]** Wei, M., Sandwell, D.T. (2010). Decorrelation of L-Band and C-Band Interferometry Over Vegetated Areas in California. *IEEE TGRS* 48(7). https://doi.org/10.1109/TGRS.2010.2043442
- ALOS PALSAR L-band kept usable coherence over vegetated terrain for much longer intervals than ENVISAT C-band.
- **Supports:** why NISAR L-band is the right choice for vegetated or tropical regions.

**[Gomba2016]** Gomba, G., Parizzi, A., De Zan, F., Eineder, M., Bamler, R. (2016). Toward Operational Compensation of Ionospheric Effects in SAR Interferograms: The Split-Spectrum Method. *IEEE TGRS* 54(3). https://doi.org/10.1109/TGRS.2015.2481079
- Separates the dispersive (ionospheric) phase from the non-dispersive (ground and troposphere) phase using sub-band interferograms. Ionospheric delay scales roughly with λ, so L-band is affected far more than C-band.

**[Fattahi2017]** Fattahi, H., Simons, M., Agram, P. (2017). InSAR Time-Series Estimation of the Ionospheric Phase Delay: An Extension of the Split Range-Spectrum Technique. *IEEE TGRS* 55(10). https://doi.org/10.1109/TGRS.2017.2718566

**[Liang2019]** Liang, C., Agram, P., Simons, M., Fielding, E.J. (2019). Ionospheric Correction of InSAR Time Series Analysis of C-band Sentinel-1 TOPS Data. *IEEE TGRS* 57(9). https://doi.org/10.1109/TGRS.2019.2908494
- **Limits (all three ionosphere papers):** in equatorial and tropical regions, an uncorrected L-band interferogram can show long-wavelength ionospheric "fringes" that look like deformation. We must say whether our interferograms are ionosphere-corrected, for example whether the NISAR GUNW product includes the correction layer. If they are not, we should only interpret short-wavelength, fault-localized signals.

## 5. Reservoir validation with ICESat-2

**[Cooley2021]** Cooley, S.W., Ryan, J.C., Smith, L.C. (2021). Human alteration of global surface water storage variability. *Nature* 591, 78–81. https://doi.org/10.1038/s41586-021-03262-3
- ICESat-2 altimetry over about 227,000 water bodies measured seasonal water-level variability. Human-managed reservoirs accounted for ~57% of global seasonal storage variability, even though they are a small share of water area *(approx.)*.
- **Supports:** using ICESat-2 heights to check that SAR-mapped area changes really are storage changes.

**[ATL13]** ICESat-2 ATL13 Inland Water Surface Height product, NSIDC DAAC. https://nsidc.org/data/atl13
- Along-track inland water surface heights. When combined with SAR area (an area–elevation curve), they give volume change. **Limits:** ICESat-2 has sparse ground tracks and a 91-day repeat, so it validates the SAR results but cannot replace them.

## 6. NISAR mission

**[Kellogg2020]** Kellogg, K., Hoffman, P., Standley, S., et al. (2020). NASA-ISRO Synthetic Aperture Radar (NISAR) Mission. *2020 IEEE Aerospace Conference*. https://doi.org/10.1109/AERO47225.2020.9172638

**[NISAR-SUH]** NISAR Science Team (2019). *NASA-ISRO SAR (NISAR) Mission Science Users' Handbook*. JPL. https://nisar.jpl.nasa.gov/documents/26/NISAR_FINAL_9-6-19.pdf
- Key specs: L-band (~24 cm, NASA) and S-band (~10 cm, ISRO); SweepSAR with a 12 m reflector and a ~240 km swath; 12-day repeat, with ~6-day sampling when ascending and descending passes are combined; global land and ice coverage; free and open data. Launched 30 July 2025.
- **Supports:** the "all-weather, every 12 days, through vegetation" pitch.

## 7. Speckle filtering

**[Lee1980]** Lee, J.-S. (1980). Digital Image Enhancement and Noise Filtering by Use of Local Statistics. *IEEE TPAMI* PAMI-2(2), 165–168. https://doi.org/10.1109/TPAMI.1980.4766994

**[Lee1981]** Lee, J.-S. (1981). Refined filtering of image noise using local statistics. *Computer Graphics and Image Processing* 15(4), 380–389. https://doi.org/10.1016/S0146-664X(81)80018-4
- Speckle is multiplicative and fully developed: a single-look intensity has standard deviation equal to its mean. Averaging N independent looks reduces the variance roughly by 1/N. The Lee filter adapts the smoothing to local statistics, so edges are preserved.
- **Supports:** multilooking or Lee filtering before thresholding. Without it, pixel-level water masks are salt-and-pepper noise.

## 8. Optical cloud cover (problem framing)

**[King2013]** King, M.D., Platnick, S., Menzel, W.P., Ackerman, S.A., Hubanks, P.A. (2013). Spatial and Temporal Distribution of Clouds Observed by MODIS Onboard the Terra and Aqua Satellites. *IEEE TGRS* 51(7), 3826–3852. https://doi.org/10.1109/TGRS.2012.2227333
- Over a decade of MODIS data, about 67% of Earth's surface was cloud-covered on average, with higher fractions over oceans and in the tropics.
- **Supports:** the opening slide. Optical sensors miss most moments, and floods come with clouds.

## 9. Global surface water

**[Pekel2016]** Pekel, J.-F., Cottam, A., Gorelick, N., Belward, A.S. (2016). High-resolution mapping of global surface water and its long-term changes. *Nature* 540, 418–422. https://doi.org/10.1038/nature20584 · Data explorer: https://global-surface-water.appspot.com/
- 32 years of Landsat at 30 m. About 90,000 km² of permanent surface water disappeared, and about 184,000 km² of new permanent water formed, much of it in reservoirs. Central Asia (the Aral Sea) accounts for a large share of the losses.
- **Supports:** using JRC GSW as the optical baseline and "historical occurrence" layer. **Limits:** it is Landsat-only, so cloud gaps leave it with no observations during floods. That is why we combine sensors at the product level: GSW history plus NISAR snapshots.

## 10. Aral Sea and Central Asian water

**[Micklin2007]** Micklin, P. (2007). The Aral Sea Disaster. *Annual Review of Earth and Planetary Sciences* 35, 47–72. https://doi.org/10.1146/annurev.earth.35.031306.140120
- Soviet-era irrigation diversions from the Amu Darya and Syr Darya shrank the sea dramatically. It lost most of its area and roughly 90% of its volume *(approx.)*, split into separate basins and became far saltier. The dust storms and health effects that followed are documented.

**[NASA-EO-Aral]** NASA Earth Observatory, *World of Change: Shrinking Aral Sea*. https://earthobservatory.nasa.gov/world-of-change/AralSea
- A MODIS/Landsat time series since 2000, including the eastern basin drying completely in 2014. Good for a public-facing visual.

---

## Q&A one-liners

1. **"Why not just use optical / Sentinel-2?"** About two-thirds of Earth is under cloud at any moment, and floods come with storms, while L-band SAR images through cloud, day and night. [King2013]
2. **"Isn't a backscatter threshold too simple?"** Automatic thresholding of calm water is the basis of operational flood services and achieves high accuracy; we add terrain and history checks the same way they do. [Martinis2009][Twele2016]
3. **"What about flooded forest?"** At L-band, flooded forest gets brighter through double-bounce, not darker, so we flag it separately or state it as a known miss. [Hess1995][Hess2003]
4. **"Your ML accuracy is inflated by spatial autocorrelation."** That's why we report leave-region-out spatial CV; random pixel CV is known to leak and overstate skill. [Roberts2017][Ploton2020]
5. **"How do you know a change is real and not speckle?"** We multilook or Lee-filter first, then test the log-ratio change against the pixel's own temporal variability, following the log-ratio and omnibus-test literature. [Lee1981][Bazi2005][Conradsen2016]
6. **"Can SAR really detect landslides?"** Yes: Sentinel-1 amplitude change has detected landslides under cloud, and we present results as density heatmaps, not exact outlines. [Mondini2019][Handwerger2022]
7. **"What does one fringe mean?"** One fringe is λ/2 of line-of-sight motion, about 12 cm for NISAR L-band, so we measure motion toward or away from the satellite, not 3-D motion. [Rosen2000][Massonnet1993]
8. **"Isn't L-band ionosphere a problem in the tropics?"** Yes. Long-wavelength ionospheric phase can mimic deformation, so we use split-spectrum-corrected products where available and otherwise only interpret localized signals. [Gomba2016][Fattahi2017]
9. **"How do you validate reservoir area?"** We cross-check against ICESat-2 ATL13 water heights through an area–elevation relationship, as was done for global reservoir storage. [Cooley2021][ATL13]
10. **"Why NISAR specifically, and why combine with JRC?"** NISAR gives L-band every 12 days, free and globally, and JRC GSW gives 30+ years of optical history, so together they give both a baseline and a revisit rate. [NISAR-SUH][Kellogg2020][Pekel2016]
