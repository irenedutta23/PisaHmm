import collections

nbins=30
#ordered with increasing priority
binningrules=[
("n.*" , "%s , 0 , 30"%nbins),
("N.*" , "%s , 0 , 30"%nbins),
(".*_pt(_|$).*" , "%s , 0 , 300"%nbins),
(".*HT.*" , "%s , 0 , 300"%nbins),
(".*_qgl" , "%s , 0 , 1"%nbins),
("QGLweight*" , "%s , 0 , 10"%nbins),
(".*_eta(_|$).*" , "%s , -5 , 5"%nbins),
(".*_phi(_|$).*" , "%s , -3.1415 , +3.1415"%nbins),
(".*_m(_|$).*" , "%s , 0,500"%nbins),
(".*_M(_|$).*" , "%s , 0,500"%nbins),
(".*_Mass(_|$).*" , "%s , 0,500"%nbins),
(".*Higgs_m.*" , "80 , 70,150"),
(".*Higgs_mReso.*" , "%s , 0,20"%(nbins)),
(".*_.*tag.*" , "%s , 0,1"%nbins),
(".*Class.*" , "%s , -1,1"%nbins),
(".*Atan.*" , "%s , 0,2"%(nbins*100)),
(".*DNN18Atan*" , "%s , 0,5"%(nbins*100)),
(".*NNAtan.*" , "%s , 0,5"%(nbins*120)),
(".*Soft.*" , "10 , -0.5,9.5"),
(".*Mqq_log.*" , "%s , 5,10"%nbins),
(".*zstar.*" , "%s , -2,2"%nbins),
(".*mmjj_pz.*" , "%s , 0,5000"%nbins),
(".*mmjj_pz_logabs.*" , "%s , 0,10"%nbins),
(".*_pt_log.*" , "%s , 0,10"%nbins),
(".*DeltaEta.*" , "%s , 0,10"%nbins),
(".*theta.*" , "%s , -1,1"%nbins),
(".*AbsEta.*" , "%s , 0,5"%nbins),
("PV_npvs.*" , "%s , 0,60"%nbins),
("LeadingSAJet_pt.*" , "%s , -10 , 150"%16),
("LHE_N.*" , "5 , -1 , 4"),
(".*balance.*" , "%s , 0 , 4"%nbins),
("minEtaHQ.*","%s , 0 , 5"%nbins),
("Rpt","%s , 0 , 1"%nbins),
("Higgs_mRelReso","%s , 0 , 0.2"%nbins),
("Jet_jetId.*","%s , 0 , %s"%(nbins,nbins-1)),
("Jet_puId.*","%s , 0 , %s"%(nbins,nbins-1)),
("fixedGridRhoFastjetAll*","40 , 0 , 40"),
("CS*","%s , -3.2 , 3.2"%nbins),
]

