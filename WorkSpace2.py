import ROOT
import os
import collections
import math
import copy
import re

##############################################################################################################
#########################  region[x] : keys are plot names, values are region names  #########################
##############################################################################################################
regionName = {"SignalRegion" : "SR", "SideBand" : "SB", "ZRegion" : "ZR", "PreSel" : "PS", }





def writeSystematic (fname, region, varName, systematicDetail, all_histo_all_syst, availableSamples, datacard, year) :

        
    f = ROOT.TFile (fname, "RECREATE")
    f.cd()
    
    for x in region.keys() : 
        hname = ""
        for samp in availableSamples[x] :
            hname = varName[x] + "_" + region[x] + "_" + samp
            h = all_histo_all_syst[x][samp]["nom"].Clone(hname)
            h.Write()
        h_data_obs = all_histo_all_syst[x]["data"+year]["nom"].Clone(varName[x]+"_"+region[x]+"_data_obs")
        h_data_obs.Write()

                
        systnameDict = {}
        for samp in availableSamples[x] :
            systnameDict[samp] = {}
            for sy in all_histo_all_syst[x][samp] :
                systnameDict[samp][sy] = sy
        
        hname = ""
        for samp in availableSamples[x] :
            for sy in all_histo_all_syst[x][samp] :

                hname = varName[x] + "_" + region[x] + "_" + samp
                hname = hname + "_" + systnameDict[samp][sy]# + ("Up" if sy.endswith("Up") else "Down")

                h = all_histo_all_syst[x][samp][sy].Clone(hname)
                h.Write()
    
    f.Close()      
    
        

    for syst in systematicDetail :
        datacard.write( writeLine(syst, systematicDetail[syst], availableSamples, region))
             
    
    
         
            
def writeLine (uncName, systematicDetailElement, allSamples, region) :
    uncType = systematicDetailElement["type"]
    sampleWithSystematic = []
    if "decorrelate" in systematicDetailElement.keys() : 
        for sl in systematicDetailElement["decorrelate"].values() :  sampleWithSystematic += sl
    else : 
        for sl in allSamples.values() :  sampleWithSystematic += sl
        sampleWithSystematic = list(set(sampleWithSystematic))
    value = 1. if "value" not in systematicDetailElement.keys()  else systematicDetailElement["value"]
    
    #print "uncName  ", uncName
    #print "uncType  ", uncType
    #print "value  ", value
    #print "allSamples  ", allSamples
    #print "sampleWithSystematic  ", sampleWithSystematic

    
    line = ""
    position = []
    orderedUncertainties = []
    
    n = 0
    for x in allSamples.keys() :
        notThisRegion = [y for y in allSamples.keys() if y!=x]
        for sl in allSamples[x] :
            orderedUncertainties.append(0)
            for s in sampleWithSystematic :

                if re.search(s+"_", sl) :  
                    if all(not re.search(regionName[region[y]]+"$", uncName) for y in notThisRegion) :
                        position.append(n)
                        if "valueFromPlots" in systematicDetailElement.keys() : orderedUncertainties[-1] =  str(systematicDetailElement["valueFromPlots"][s])[:7]
                        else : orderedUncertainties[-1] =  value
            n+=1
    
    
    if len(position)==0 : return ""

    line += uncName + "\t"*(3 - len(uncName)/8)
    line += uncType + "\t"*(2 - len(uncType)/8)
    line += writeUncertainities (orderedUncertainties, len(orderedUncertainties), position)

    return line + "\n";








def writeUncertainities (orderedUncertainties, lenght, position) :
    uncLine= ""; 
    for n in range(lenght) :
        if n in position :
            uncLine += str(orderedUncertainties[n])
        else : 
            uncLine += "-"
        uncLine += "\t\t\t"
    
    return uncLine
    

    

def printSystematicGrouping (systematicDetail, outputFile = "groupingCheck.py") :

    outputName = open(outputFile, 'w')
    print >> outputName , '{'
    
    for syst in systematicDetail : 
        print >> outputName , '"'+syst+'" : {'
        for k in systematicDetail[syst] :
            print >> outputName , '\t"'+k+'" : ', systematicDetail[syst][k], ','
        print >> outputName , '}'
    
    print >> outputName , '}'



def divideShapeAndNormalization (systematicDetail) :
        
    systKeys = systematicDetail.keys()
    for syst in systKeys :
        if "shapeAndNorm" == systematicDetail[syst]["type"] :
            systematicDetail[syst+"Shape"] = copy.deepcopy(systematicDetail[syst])
            systematicDetail[syst+"Shape"]["type"] =  "shapeOnly"
            systematicDetail[syst]["type"] = "normalizationOnly"


def decorrelateNormOnly (systematicDetail, availableSamples) :
    
    systKeys = systematicDetail.keys()
    for syst in systKeys :
        if "normalizationOnly" in systematicDetail[syst].keys() and "decorrelate" not in systematicDetail[syst].keys():
            systematicDetail[syst]["decorrelate"] = {}
            for x in availableSamples : systematicDetail[syst]["decorrelate"][x] = x
    


def modifySystematicDetail(systematicDetail, listAllSample_noYear) :
    
    systKeys = systematicDetail.keys()
    for syst in systKeys :
        if "decorrelate" not in systematicDetail[syst].keys() :
            systematicDetail[syst]["decorrelate"] = {"all" : listAllSample_noYear}
        
        prima = [len(systematicDetail[syst]["decorrelate"][g]) for g in systematicDetail[syst]["decorrelate"]]
        for g in systematicDetail[syst]["decorrelate"].keys() : 
            systematicDetail[syst]["decorrelate"][g] = [s for s in systematicDetail[syst]["decorrelate"][g] if s in listAllSample_noYear]

        keys = systematicDetail[syst]["decorrelate"].keys()
        for g in keys :
            if len(systematicDetail[syst]["decorrelate"][g]) == 0 : 
                systematicDetail[syst]["decorrelate"].pop(g, None)
          
        if len(systematicDetail[syst]["decorrelate"])==0 : systematicDetail.pop(syst, None)
        elif len(systematicDetail[syst]["decorrelate"].keys()) > 1:
            for g in systematicDetail[syst]["decorrelate"] :
                systematicDetail[syst+g] =copy.deepcopy(systematicDetail[syst])
                systematicDetail[syst+g].pop("decorrelate", None)
                systematicDetail[syst+g]["decorrelate"] = {g : systematicDetail[syst]["decorrelate"][g]}
            systematicDetail.pop(syst, None)
    

def removeUnusedSystematics(systematicDetail, all_histo_all_syst) :
    
    systKeys = systematicDetail.keys()
    for syst in systKeys :
        if re.search("shape", systematicDetail[syst]["type"]) or re.search("normalizationOnly", systematicDetail[syst]["type"]) :
            x    = all_histo_all_syst.keys()[0]
            samp = all_histo_all_syst[x].keys()[0]
            #print "removeUnusedSystematics  ", syst, " \t ",all_histo_all_syst[x][samp].keys()
            
            sample = systematicDetail[syst]["decorrelate"].keys()[0]
            sysNoVarname = re.sub("Shape", "", re.sub(sample, "", syst))

            #if all( not re.search(sysNoVarname, s) for s in all_histo_all_syst[x][samp].keys() ) :
            if all( not re.search(re.sub("Up", "", re.sub("Down", "", s)), syst) for s in all_histo_all_syst[x][samp].keys() ) :
                systematicDetail.pop(syst, None)
                print "removed ", syst
            

        
        

def ScaleShapeOnlyPlot(systematicDetail, all_histo_all_syst) :

    systKeys = systematicDetail.keys()
    for syst in systKeys :
        if systematicDetail[syst]["type"] == "shapeOnly" : 
            systematicDetail[syst]["type"] = "shape"
            for x in all_histo_all_syst.keys() :
                for samp in all_histo_all_syst[x] :
                    for s in all_histo_all_syst[x][samp].keys() :
                        if re.search(re.sub("Up", "", re.sub("Down", "", s)), syst) :
                            if all_histo_all_syst[x][samp][s].Integral()>0 : all_histo_all_syst[x][samp][s].Scale(  all_histo_all_syst[x][samp]["nom"].Integral() / all_histo_all_syst[x][samp][s].Integral() )
    
    

def valuesFromPlots(systematicDetail, all_histo_all_syst, region) :
    
    for syst in systematicDetail.keys() :
        if systematicDetail[syst]["type"] == "normalizationOnly" :
            systematicDetail[syst]["type"] = "lnN"
            systematicDetail[syst]["valueFromPlots"] = {}
                
            for x in all_histo_all_syst.keys() :
                systematicDetail[syst+"_"+regionName[region[x]]] = copy.deepcopy(systematicDetail[syst])
                
                
                for sKey in systematicDetail[syst]["decorrelate"] :
                    for s in systematicDetail[syst]["decorrelate"][sKey] : 
                        value = 0.
                        for samp in all_histo_all_syst[x] :
                            if re.search(s+"_", samp) :
                                systName = ""
                                systName = syst[:-len(sKey)]
                                Nbins = all_histo_all_syst[x][samp]["nom"].GetNbinsX()+1
                                variationUp   = 1. if all_histo_all_syst[x][samp]["nom"].Integral(0,Nbins)<=0           else all_histo_all_syst[x][samp][systName+"Up"].Integral(0,Nbins) / all_histo_all_syst[x][samp]["nom"].Integral(0,Nbins)
                                variationDown = 1. if all_histo_all_syst[x][samp][systName+"Down"].Integral(0,Nbins)<=0 else all_histo_all_syst[x][samp]["nom"].Integral(0,Nbins)         / all_histo_all_syst[x][samp][systName+"Down"].Integral(0,Nbins)
                                value = (variationUp + variationDown)/2.

                        systematicDetail[syst+"_"+regionName[region[x]]]["valueFromPlots"][s] = value   
                        
                        
                        
            
            systematicDetail.pop(syst, None)


def SumErrors(v1, v2) :
    #print "valori", v1, v2
    return math.exp( ( (math.log(v1))**2. + (math.log(v2))**2. )**0.5  )
    
    


def mergeTwoSystematics(systematicDetail, syst1, syst2, listAllSample_noYear) :
    

        samples1 = systematicDetail[syst1]["decorrelate"].values()[0]     # "decorrelate" has just one key
        samples2 = systematicDetail[syst2]["decorrelate"].values()[0]
        #newDecorrelate = list(set(samples1+samples2))
        
        
        if "valueFromPlots" not in systematicDetail[syst2].keys() : 
            systematicDetail[syst2]["valueFromPlots"] = {}
            for s in samples2 : systematicDetail[syst2]["valueFromPlots"][s] = 1. if "value" not in systematicDetail[syst2].keys() else systematicDetail[syst2]["value"]
        if "valueFromPlots" not in systematicDetail[syst1].keys() : 
            systematicDetail[syst1]["valueFromPlots"] = {}
            for s in samples1 : systematicDetail[syst1]["valueFromPlots"][s] = 1. if "value" not in systematicDetail[syst1].keys() else systematicDetail[syst1]["value"]
        
        #print syst1, "    \t ", systematicDetail[syst1]["decorrelate"]
        #print "valueFromPlots \t ", systematicDetail[syst1]["valueFromPlots"]
        #print syst2, "    \t ", systematicDetail[syst2]["decorrelate"]
        #print "valueFromPlots \t ", systematicDetail[syst2]["valueFromPlots"]
        
        newValues = {}
        for s in samples1 : 
            #print "check   ", s, 1 if s not in samples1 else systematicDetail[syst1]["valueFromPlots"][s],  1 if s not in samples2 else systematicDetail[syst2]["valueFromPlots"][s]
            newValues[s] = SumErrors(1 if s not in samples1 else systematicDetail[syst1]["valueFromPlots"][s],
                                                           1 if s not in samples2 else systematicDetail[syst2]["valueFromPlots"][s]
                                                           )
        systematicDetail[syst1]["decorrelate"]       = {"merged" : samples1}
        systematicDetail[syst1]["valueFromPlots"]    = newValues
    
        #systematicDetail.pop(syst2, None)



def mergeToSys(systematicDetail, listAllSample_noYear) :
        
    systKeys = systematicDetail.keys()
    mergedSystematic = [] # the pop() cannot be done on the fly because several systematics can have identical "mergeToSys"
    for syst in systKeys :
        if "mergeWith" in systematicDetail[syst].keys() :
            sysTomergeList = systematicDetail[syst]["mergeWith"]
            for s in sysTomergeList :
                for sysTomerge in systKeys :
                    if re.search(s, sysTomerge) :
                #if sysTomerge in systKeys : 
                        if systematicDetail[syst]["type"] == "lnN" and  systematicDetail[sysTomerge]["type"] == "lnN" : 
                            mergedSystematic.append(sysTomerge)
                            mergeTwoSystematics(systematicDetail, syst, sysTomerge, listAllSample_noYear)
                
    for s in set(mergedSystematic) : systematicDetail.pop(s, None)




def createWorkSpace(model, all_histo_all_syst, year) :
    print "WorkSpace creation"
    nBins = {}
    varName = {}
    plotName = {}  #it will be equal to varName because of how plot.py write all_histo_all_syst
    region = {}
    
    
    print  all_histo_all_syst.keys() 
    for x in all_histo_all_syst.keys() : 
        nBins[x] = all_histo_all_syst[x]["data"+year]["nom"].GetNbinsX()-1
        varName[x] = all_histo_all_syst[x]["data"+year]["nom"].GetName().split("___")[0]
        plotName[x] = x
        region[x] = x.split("___")[-1]  # keys are plot names, values are region names
    
    region = collections.OrderedDict(sorted(region.items()))
    
    os.system("mkdir -p workspace")
    datacard=open("workspace/datacard"+year+model.name+".txt","w")
    
    datacard.write("imax "+str(len(all_histo_all_syst.keys()))+"  number of channels\n")
    datacard.write("jmax *  number of backgrounds\n")
    datacard.write("kmax *  number of nuisance parameters (sources of systematical uncertainties)\n")
    datacard.write("------------\n")
    for x in region : datacard.write("shapes * "+region[x]+"  fileCombine"+year+model.name+".root "+varName[x]+"_$CHANNEL_$PROCESS "+varName[x]+"_$CHANNEL_$PROCESS_$SYSTEMATIC\n")
    datacard.write("------------\n")
    datacard.write("bin \t\t")
    for x in region : datacard.write(region[x] + " \t" )
    datacard.write("\nobservation \t")
    for x in region : datacard.write(str(all_histo_all_syst[x]["data"+year]["nom"].Integral(0, nBins[x]+1)) + " \t\t" )
    datacard.write("\n------------\n")

    listSig  = []
    listBkg  = []
    for s in  model.signal :        listSig = listSig + model.signal[s]
    for s in  model.background :    listBkg = listBkg + model.background[s]
    
    listAllSample = listSig + listBkg
    availableSamples = {}
    processNumber = {}
    for n in range(len(listSig)) : processNumber[listSig[n]] = -n
    for n in range(len(listBkg)) : processNumber[listBkg[n]] = n+1
        #if listBkg[n].startswith("EWK") : processNumber[listBkg[n]] = -n
        #else : processNumber[listBkg[n]] = n+1
    
    #remove samples with no predicted events
    emptySamples = {}
    for x in region : 
        emptySamples[x] = []
        for s in listAllSample :
            if not all(all_histo_all_syst[x][s][sy].Integral(0, nBins[x]+1) > 0. for sy in all_histo_all_syst[x][s].keys()) : emptySamples[x].append(s)
        availableSamples[x] = [ s for s in listAllSample if s not in emptySamples[x]]

    listAllSample_noYear = [s.split("_")[0] for s in listAllSample]
    availableSamples = collections.OrderedDict(sorted(availableSamples.items()))

    datacard.write("bin \t \t \t \t \t")
    for x in region : 
        for s in availableSamples[x] :
            datacard.write(region[x]+" \t\t")
        
    datacard.write("\nprocess \t \t \t \t")
    for x in region : 
        for s in availableSamples[x] :
            datacard.write(s+"\t"+("" if len(s)>15 else "\t"))
        
    datacard.write("\nprocess \t \t \t \t")
    for x in region : 
        for s in availableSamples[x] :
            datacard.write(str(processNumber[s])+"\t\t\t")
        
    datacard.write("\nrate \t \t \t \t \t")
    for x in region : 
        for s in availableSamples[x] :
            datacard.write(str(all_histo_all_syst[x][s]["nom"].Integral(0, nBins[x]+1))+"\t\t")
    datacard.write("\n------------\n")



    #print "region ", region
    #print "varName ", varName
    #print "availableSamples ", availableSamples
    #print "\n ---------------------------- \n" 




    divideShapeAndNormalization (model.systematicDetail) 
    #decorrelateNormOnly (model.systematicDetail, availableSamples) 

    modifySystematicDetail(model.systematicDetail, listAllSample_noYear) 
    #printSystematicGrouping (model.systematicDetail, "grouping0.py") 
    
    
    removeUnusedSystematics(model.systematicDetail, all_histo_all_syst) 
    #printSystematicGrouping (model.systematicDetail, "grouping1.py") 
    
    
    valuesFromPlots(model.systematicDetail, all_histo_all_syst, region)
    #printSystematicGrouping (model.systematicDetail, "grouping2.py") 
    
    
    ScaleShapeOnlyPlot(model.systematicDetail, all_histo_all_syst) 
    #printSystematicGrouping (model.systematicDetail, "grouping3.py") 
    
    
    mergeToSys(model.systematicDetail, listAllSample_noYear) 
    #printSystematicGrouping (model.systematicDetail, "grouping4.py") 



        
    writeSystematic ("workspace/fileCombine"+year+model.name+".root", region, varName, model.systematicDetail, all_histo_all_syst, availableSamples, datacard, year) 



    for x in region.keys() : datacard.write( region[x]+" autoMCStats 0 1\n\n")
    

    
    print "WorkSpace end"
    
    
    
