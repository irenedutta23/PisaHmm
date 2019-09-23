from nail.nail import *
import ROOT
nthreads=50
import sys
import copy
ROOT.gROOT.ProcessLine(".x softactivity.h")

ROOT.gInterpreter.AddIncludePath("/scratch/lgiannini/HmmPisa/lwtnn/include/lwtnn") 
ROOT.gSystem.Load("/scratch/lgiannini/HmmPisa/lwtnn/build/lib/liblwtnn.so")

from eventprocessing import flow
from histograms import histosPerSelection,histosPerSelectionFullJecs

used=[]
for s in histosPerSelection:
    used.append(s)
    used.extend(histosPerSelection[s])
used=list(set(used))

ftxt=open("out/description.txt","w")
ftxt.write(flow.Describe(used))

snap=[] 
snaplist=["nJet","Higgs_m","QJet0_qgl","QJet1_qgl","QJet0_eta","QJet1_eta","Mqq","Higgs_pt","Mu0_pt","Mu0_corrected_pt","Mu1_corrected_pt","Mu1_pt","Mu0_eta","Mu1_eta","Mu1_phi","Mu0_phi","nGenPart","GenPart_pdgId","GenPart_eta","GenPart_phi","GenPart_pt"]#,"twoJets","twoOppositeSignMuons","PreSel","VBFRegion","MassWindow","SignalRegion","qqDeltaEta","event","HLT_IsoMu24","QJet0_pt_nom","QJet1_pt_nom","QJet0_puId","QJet1_puId","SBClassifier","Higgs_m","Mqq_log","mmjj_pt_log","NSoft5","ll_zstar","theta2","mmjj_pz_logabs","MaxJetAbsEta","ll_zstar_log"]#,"QJet0_prefireWeight","QJet1_prefireWeight","PrefiringCorrection","CorrectedPrefiringWeight"]
#snaplist=["QJet0_prefireWeight","QJet1_prefireWeight","PrefiringCorrection","CorrectedPrefiringWeight"]

from histobinning import binningrules
flow.binningRules = binningrules

flowData=copy.deepcopy(flow)
procData=flowData.CreateProcessor("eventProcessorData",snaplist+["QGLweight"],histosPerSelection,snap,"SignalRegion",nthreads)

#define some event weights
from weights import *
addDefaultWeights(flow)
addMuEffWeight(flow)
addQGLweight(flow)
addPreFiring(flow)

from systematics import *

addLheScale(flow)
addLhePdf(flow)
addPSWeights(flow)
addBtag(flow)
addBasicJecs(flow)
addMuScale(flow)
addPUvariation(flow)
addReweightEWK(flow)
addQGLvariation(flow)
addPreFiringVariation(flow)


snaplist+=["genWeight","puWeight","btagWeight","muEffWeight","QJet1_partonFlavour","QJet0_partonFlavour"]
systematics=flow.variations #take all systematic variations
print "Systematics for all plots", systematics
histosWithSystematics=flow.createSystematicBranches(systematics,histosPerSelection)
#addPtEtaJecs(flow)

addDecorrelatedJER(flow)
addCompleteJecs(flow)
histosWithFullJecs=flow.createSystematicBranches(systematics,histosPerSelectionFullJecs)

for region in histosWithFullJecs:
   if region not in histosWithSystematics :
	histosWithSystematics[region]=histosWithFullJecs[region]
   else:
	histosWithSystematics[region]=list(set(histosWithSystematics[region]+histosWithFullJecs[region]))

print "The following histograms will be created in the following regions"
for sel in  histosWithSystematics:
	print sel,":",histosWithSystematics[sel]
print >> sys.stderr, "Number of known columns", len(flow.validCols)

#pproc=flow.CreateProcessor("eventProcessor",snaplist,histosWithSystematics,snap,"SignalRegion",nthreads)
proc=flow.CreateProcessor("eventProcessor",snaplist,histosWithSystematics,snap,"",nthreads)



from samples2016 import samples as samples2016
from samples2017 import samples as samples2017
from samples2018 import samples as samples2018

year=sys.argv[1]
if year == "2016":
   samples=samples2016
   trigger="HLT_IsoMu24 || HLT_IsoTkMu24"
if year == "2017":
   samples=samples2017
   trigger="HLT_IsoMu27"
if year == "2018":
   samples=samples2018
   trigger="HLT_IsoMu24"
 

from samplepreprocessing import flow as preflow
specificPreProcessors={}
specificPostProcessors={}
for s in samples :
   if "filter" in samples[s].keys():
	print "Specific pre processor for" ,s
	specificPreProcessors[s]=preflow.CreateProcessor(s+"Processor",[samples[s]["filter"]],{samples[s]["filter"]:[samples[s]["filter"]]},[],samples[s]["filter"],nthreads)
   if "postproc" in samples[s].keys():
       print "Specific post processor for" ,s
       flowSpec=copy.deepcopy(flow)
       specificPostProcessors[s]=samples[s]["postproc"](flowSpec,proc.produces,histosWithSystematics,snaplist,snap,nthreads)

	
import psutil
def f(ar):
#f,s,i=ar
     p = psutil.Process()
     print "Affinity",p.cpu_affinity()
     p.cpu_affinity( list(range(psutil.cpu_count())))
     ROOT.gROOT.ProcessLine('''
     ROOT::EnableImplicitMT(%s);
     '''%nthreads)
     s,f=ar
     print f
     rf=ROOT.TFile.Open(f[0])
     ev=rf.Get("Events")
     hessian=False
     if ev :
	 br =ev.GetBranch("LHEPdfWeight")
	 if br and "306000" in br.GetTitle():	
	    print "Sample",s,"has Hessian PDF"
	    hessian = True

     vf=ROOT.vector("string")()
     map(lambda x : vf.push_back(x), f)
     for x in vf:
	print x
     import jsonreader 
     rdf=ROOT.RDataFrame("Events",vf) #.Range(10000)
     if rdf :
       try:
	 rdf=rdf.Define("year",year)
	 rdf=rdf.Define("TriggerSel",trigger)
	 if "lumi" in samples[s].keys()  :
	   rdf=rdf.Filter("passJson(run,luminosityBlock)","jsonFilter")
	   rdf=rdf.Define("isMC","false")
	   rdf=rdf.Define("isHerwig","false")
	   if year != "2018": rdf=rdf.Define("Jet_pt_nom","Jet_pt")
	   rdf=rdf.Define("LHE_NpNLO","0")
	   rdf=rdf.Define("Jet_partonFlavour","ROOT::VecOps::RVec<int>(nJet, 0)")
	 else :
	   print "Is herwig?",("true" if "HERWIG" in s else "false"), s
	   rdf=rdf.Define("isHerwig",("true" if "HERWIG" in s else "false"))
	   if  s in  ["DY0J_2018AMCPY","DY0J_2017AMCPY","DY1J_2017AMCPY","DY1J_2018AMCPY"] :
	       rdf=rdf.Define("lhefactor","2.f") 
	   else:
	       rdf=rdf.Define("lhefactor","1.f") 
	   if "LHEPdfWeight" not in list(rdf.GetColumnNames()):
	       print "ADDING FAKE PDF",f
	       rdf=rdf.Define("LHEPdfWeight","ROOT::VecOps::RVec<float>(1,1)")
	       rdf=rdf.Define("nLHEPdfWeight","uint32_t(1)")
	   if hessian:
	       print "Setting LHEPdfHasHessian to true"
	       rdf=rdf.Define("LHEPdfHasHessian","true")
	   else:
	       print "Setting LHEPdfHasHessian to false"
	       rdf=rdf.Define("LHEPdfHasHessian","false")
           if year == "2016":
               rdf=rdf.Define("Muon_sf","(20.1f/36.4f*Muon_ISO_SF + 16.3f/36.4f*Muon_ISO_eraGH_SF)*(20.1f/36.4f*Muon_ID_SF + 16.3f/36.4f*Muon_ID_eraGH_SF)")
           else :
               rdf=rdf.Define("Muon_sf","Muon_ISO_SF*Muon_ID_SF")
	   if "btagWeight_DeepCSVB" in  list(rdf.GetColumnNames()) :
               rdf=rdf.Define("btagWeight","btagWeight_DeepCSVB")
	   else :
               rdf=rdf.Define("btagWeight","btagWeight_CMVA")
	
	   rdf=rdf.Define("isMC","true")
	   if "LHEWeight_originalXWGTUP" not in list(rdf.GetColumnNames()):
	       rdf=rdf.Define("LHEWeight_originalXWGTUP","genWeight")
	   if "LHEScaleWeight" not in list(rdf.GetColumnNames()):
	       print "ADDING FAKE LHE",f
	       rdf=rdf.Define("LHEScaleWeight","ROOT::VecOps::RVec<float>(9,1)")
	       rdf=rdf.Define("nLHEScaleWeight","uint32_t(0)")
	   if "PSWeight" not in list(rdf.GetColumnNames()):
	       print "ADDING FAKE PS WEIGHT",f
	       rdf=rdf.Define("PSWeight","ROOT::VecOps::RVec<float>(9,1)")
	       rdf=rdf.Define("nPSWeight","uint32_t(1)")
	   if "LHE_NpNLO" not in list(rdf.GetColumnNames()):
	       rdf=rdf.Define("LHE_NpNLO","-1")

	 if s.startswith("EWKZ_") and s.endswith("MGPY") : 
             #rdf=rdf.Define("EWKreweight","weightSofAct5(1)")
             rdf=rdf.Define("EWKreweight","weightGenJet(nGenJet)")
         else :
             rdf=rdf.Define("EWKreweight","1.f")
	 
	 if "filter" in samples[s] :
	   print "Prefiltering",s
           rdf=specificPreProcessors[s](rdf).rdf
	   rdf=rdf.Filter(samples[s]["filter"])

	 if "lumi" in samples[s].keys() :
   	    ou=procData(rdf)
	 else :
            ou=proc(rdf)
	 ouspec=None
         if s in specificPostProcessors.keys():
	    print "adding postproc",s
	    ouspec=specificPostProcessors[s](ou.rdf)
	    print "added"
         #snaplist=["nJet","nGenJet","Jet_pt_touse","GenJet_pt","Jet_genJetIdx","Jet_pt_touse","Jet_pt","Jet_pt_nom","Jet_genPt","LHERenUp","LHERenDown","LHEFacUp","LHEFacDown","PrefiringWeight","DNN18Atan","QJet0_prefireWeight","QJet1_prefireWeight", "QJet0_pt_touse","QJet1_pt_touse","QJet0_eta","QJet1_eta","QGLweight","genWeight","btagWeight","muEffWeight"]
#"QJet0_pt_touse","QJet1_pt_touse","QJet0_eta","QJet1_eta","Mqq","Higgs_pt","twoJets","twoOppositeSignMuons","PreSel","VBFRegion","MassWindow","SignalRegion"]

 #        snaplist=["nJet","SelectedJet_pt_touse","Jet_pt","Jet_pt_nom","Jet_puId","Jet_eta","Jet_jetId","PreSel","VBFRegion","MassWindow","SignalRegion","jetIdx1","jetIdx2","Jet_muonIdx1","Jet_muonIdx2","LHEPdfUp","LHEPdfDown","LHEPdfSquaredSum","LHEPdfRMS","nLHEPdfWeight","LHEPdfWeight","PrefiringWeight","DNN18Atan__syst__MuScaleDown","Higgs_eta__syst__MuScaleUp","Higgs_mRelReso__syst__MuScaleUp","Higgs_mReso__syst__MuScaleUp","Higgs_m__syst__MuScaleUp","Higgs_pt__syst__MuScaleUp","Mqq","Mqq_log","NSoft5__syst__MuScaleUp","QJet0_eta","QJet0_phi","QJet0_pt_touse","QJet0_qgl","QJet1_eta","QJet1_phi","QJet1_pt_touse","QJet1_qgl","Rpt__syst__MuScaleUp","event","ll_zstar__syst__MuScaleUp","minEtaHQ__syst__MuScaleUp","qqDeltaEta"]
         branchList = ROOT.vector('string')()
	 map(lambda x : branchList.push_back(x), snaplist)
 #        if "lumi" not in samples[s].keys()  :
#         rep=ou.rdf.Filter("twoMuons","twoMuons").Filter("twoOppositeSignMuons","twoOppositeSignMuons").Filter("twoJets","twoJets").Filter("MassWindow","MassWindow").Filter("VBFRegion","VBFRegion").Filter("PreSel","PreSel").Filter("SignalRegion","SignalRegion").Report() 
#	 print "Cutflow for",s
#	 rep.Print()
 #        ou.rdf.Filter("twoMuons","twoMuons").Filter("twoOppositeSignMuons","twoOppositeSignMuons").Filter("twoJets","twoJets").Snapshot("Events","out/%sSnapshot.root"%(s),branchList)
#         ou.rdf.Filter("twoMuons","twoMuons").Filter("twoOppositeSignMuons","twoOppositeSignMuons").Filter("twoJets","twoJets").Filter("MassWindow","MassWindow").Filter("VBFRegion","VBFRegion").Filter("PreSel","PreSel").Filter("SignalRegion","SignalRegion").Snapshot("Events","out/%sSnapshot.root"%(s),branchList)
#         ou.rdf.Filter("twoJets","twoJets").Filter("VBFRegion","VBFRegion").Filter("twoMuons__syst__MuScaleDown","twoMuons__syst__MuScaleDown").Filter("twoOppositeSignMuons__syst__MuScaleDown","twoOppositeSignMuons__syst__MuScaleDown").Filter("PreSel__syst__MuScaleDown","PreSel__syst__MuScaleDown").Filter("MassWindow__syst__MuScaleDown","MassWindow__syst__MuScaleDown").Filter("SignalRegion__syst__MuScaleDown","SignalRegion__syst__MuScaleDown").Snapshot("Events","out/%sSnapshot.root"%(s),branchList)
         #ou.rdf.Filter("event==63262831 || event == 11701422 || event== 60161978").Snapshot("Events","out/%sEventPick.root"%(s),branchList)
         print ou.histos.size()#,ouspec.histos.size()
         fff=ROOT.TFile.Open("out/%sHistos.root"%(s),"recreate")
         ROOT.gROOT.ProcessLine('''
     ROOT::EnableImplicitMT(%s);
     '''%nthreads)
         

         normalization = ou.rdf.Filter("twoJets","twoJets").Mean("QGLweight").GetValue()#1./(ou.rdf.Filter("twoJets","twoJets").Mean("QGLweight").GetValue())
	 if ouspec is not None :
	    print "Postproc hisots"
            for h in ouspec.histos :
                h.GetValue()
                fff.cd()
                h.Scale(1./normalization)
                h.Write()
         for h in ou.histos : 
#	    print "histo"
	    h.GetValue()
	    fff.cd()
            h.Scale(1./normalization)
 	    h.Write()
	 
         fff.Write()
         fff.Close()
	 return 0
       except Exception, e: 
	 print e
	 print "FAIL",f
	 return 1
     else :
	print "Null file",f

#     return  os.system("./eventProcessor %s %s out/%s%s "%(4,f,s,i))  

#from multiprocessing.pool import ThreadPool as Pool
from multiprocessing import Pool
runpool = Pool(5)

print samples.keys()
sams=samples.keys()

#sams=["DY2J","TTlep"]
#toproc=[(x,y,i) for y in sams for i,x in enumerate(samples[y]["files"])]
toproc=[ (s,samples[s]["files"]) for s in sams  if os.path.exists(samples[s]["files"][0])]
toproc=sorted(toproc,key=lambda x : sum(map( lambda x : ( os.path.getsize(x) if os.path.exists(x) else 0 ),x[1])),reverse=True)
print toproc

if len(sys.argv[2:]) :
   if sys.argv[2] == "fix" :
       toproc=[]
       for s in sams :
	if os.path.exists(samples[s]["files"][0]) :
	 try:
	   ff=ROOT.TFile.Open("out/%sHistos.root"%s)
	   if ff.IsZombie() or len(ff.GetListOfKeys()) == 0:
	           print "zombie or zero keys",s
	           toproc.append((s,samples[s]["files"]))
	 
	 except:
	   print "failed",s
	   toproc.append((s,samples[s]["files"]))
   else:
       toproc=[ (s,samples[s]["files"]) for s in sams if s in sys.argv[2:]]

print "Will process", toproc
   
results=zip(runpool.map(f, toproc ),[x[0] for x in toproc])
print "Results",results
print "To resubmit",[x[1] for x in results if x[0] ]
