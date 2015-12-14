#!/usr/bin/env python

import Bio.PDB
import sys
import os
import re
import numpy as np
from Bio.SVDSuperimposer import SVDSuperimposer
from math import sqrt


def parse_fnat(fnat_out):
    fnat=0;
    inter=[]
    for line in fnat_out:
#        print line
        line=line.rstrip('\n')
        match=re.search(r'NATIVE: (\d+)(\w) (\d+)(\w)',line)
        if(re.search(r'^Fnat',line)):
            list=line.split(' ')
            fnat=list[3]
            nat_correct=list[1]
            nat_total=list[2]
        elif(re.search(r'^Fnonnat',line)):
            list=line.split(' ')
            fnonnat=list[3]
            nonnat_count=list[1]
            model_total=list[2]    
        elif(match):
            #print line
            res1=match.group(1)
            chain1=match.group(2)
            res2=match.group(3)
            chain2=match.group(4)
           # print res1 + ' ' + chain1 + ' ' + res2 + ' ' + chain2
            inter.append(res1 + chain1)
            inter.append(res2 + chain2)
    return (fnat,nat_correct,nat_total,fnonnat,nonnat_count,model_total,inter)

def capri_class(fnat,iRMS,LRMS):

    if(fnat < 0.1 or (LRMS > 10 and iRMS>=4.0)):
        return 'Incorrect'
    elif((fnat >=0.1 and fnat <0.3) and (LRMS <=10 or iRMS <=4) or (fnat >= 0.3 and LRMS > 5 and iRMS > 2)):
        return 'Acceptable'
    elif((fnat >=0.3 and fnat <0.5) and (LRMS <=5 or iRMS <= 2) or (fnat >=0.5 and LRMS >1 and iRMS > 1)):
        return 'Medium'
    elif(fnat >=0.5 and (LRMS < 1 or iRMS < 1)):
        return 'High'
    else:
        return 'Undef'



def capri_class_DockQ(DockQ):

    (c1,c2,c3)=(0.23,0.49,0.80)
    if(DockQ< c1):
        return 'Incorrect'
    elif(DockQ>=c1 and DockQ<=c2):
        return 'Acceptable'
    elif(DockQ>=c2 and DockQ<=c3):
        return 'Medium'
    elif(DockQ>c3):
        return 'High'
    else:
        return 'Undef'


exec_path=os.path.dirname(os.path.abspath(sys.argv[0]))
model=sys.argv[1]
native=sys.argv[2]
use_CA_only=False


atom_for_sup=['CA','C','N','O']
if(use_CA_only):
    atom_for_sup=['CA']




cmd_fnat=exec_path + '/fnat ' + model + ' ' + native + ' 5'
cmd_interface=exec_path + '/fnat ' + model + ' ' + native + ' 10 backbone'


fnat_out = os.popen(cmd_fnat).readlines()
(fnat,nat_correct,nat_total,fnonnat,nonnat_count,model_total,interface5A)=parse_fnat(fnat_out)
inter_out = os.popen(cmd_interface).readlines()
(fnat_bb,nat_correct_bb,nat_total_bb,fnonnat_bb,nonnat_count_bb,model_total_bb,interface)=parse_fnat(inter_out)

#Use same interface as for fnat for iRMS
#interface=interface5A
          

# Start the parser
pdb_parser = Bio.PDB.PDBParser(QUIET = True)

# Get the structures
ref_structure = pdb_parser.get_structure("reference", native)
sample_structure = pdb_parser.get_structure("model", model)

# Use the first model in the pdb-files for alignment
# Change the number 0 if you want to align to another structure
ref_model    = ref_structure[0]
sample_model = sample_structure[0]

# Make a list of the atoms (in the structures) you wish to align.
# In this case we use CA atoms whose index is in the specified range
ref_atoms = []
sample_atoms = []

common_interface=[]
chain_res={}

# Do the same for the sample structure
for sample_chain in sample_model:
  chain=sample_chain.id
  if chain not in chain_res.keys():
      chain_res[chain]=[]
  for sample_res in sample_chain:
    resname=sample_res.get_id()[1]
    key=str(resname) + chain
#    print key
    chain_res[chain].append(key)
#    chain_res[chain].append(sample_res)
    if key in interface:
 #     print key
      for a in atom_for_sup:  
 #         sample_atoms.append(sample_res['CA'])
        sample_atoms.append(sample_res[a])
                        
      common_interface.append(key)

#print inter_pairs

chain_ref={}
common_residues=[]
# Iterate of all chains in the model in order to find all residues
for ref_chain in ref_model:
  # Iterate of all residues in each model in order to find proper atoms
#  print dir(ref_chain)
  chain=ref_chain.id
  if chain not in chain_ref.keys():
      chain_ref[chain]=[]
  for ref_res in ref_chain:
      resname=ref_res.get_id()[1]
      key=str(resname) + chain
      #print ref_res
#      print key
     # print chain_res.values()
      if key in chain_res[chain]: # if key is present in sample
          #print key
          for a in atom_for_sup:  
              chain_ref[chain].append(ref_res[a])
          common_residues.append(key)
          #chain_sample.append((ref_res['CA'])
      if key in common_interface:
      # Check if residue number ( .get_id() ) is in the list
      # Append CA atom to list
        #print key  
        for a in atom_for_sup:
            ref_atoms.append(ref_res[a])
            

#get the ones that were present in native        
chain_sample={}
for sample_chain in sample_model:
  chain=sample_chain.id
  if chain not in chain_sample.keys():
      chain_sample[chain]=[]
  for sample_res in sample_chain:
    resname=sample_res.get_id()[1]
    key=str(resname) + chain
    if key in common_residues:
        for a in atom_for_sup:
            chain_sample[chain].append(sample_res[a])

    #if key in common_residues:
 #     print key  
      #sample_atoms.append(sample_res['CA'])
      #common_interface.append(key)

        
#print ref_atoms
#print sample_atoms
#print sample_model.get_atoms()
# Now we initiate the superimposer:
super_imposer = Bio.PDB.Superimposer()
super_imposer.set_atoms(ref_atoms, sample_atoms)
super_imposer.apply(sample_model.get_atoms())

# Print RMSD:
irms=super_imposer.rms

(chain1,chain2)=chain_sample.keys()

ligand_chain=chain1
receptor_chain=chain2
len1=len(chain_sample[chain1])
len2=len(chain_sample[chain2])
class1='ligand'
class2='receptor'
if(len(chain_sample[chain1]) > len(chain_sample[chain2])):
    receptor_chain=chain1
    ligand_chain=chain2
    class1='receptor'
    class2='ligand'


#print chain_sample.keys()

#Set to align on receptor
super_imposer.set_atoms(chain_ref[receptor_chain], chain_sample[receptor_chain])
super_imposer.apply(sample_model.get_atoms())
receptor_chain_rms=super_imposer.rms
#print receptor_chain_rms
#print dir(super_imposer)
#print chain1_rms

#Grep out the transformed ligand coords

coord1=np.array([atom.coord for atom in chain_ref[ligand_chain]])
coord2=np.array([atom.coord for atom in chain_sample[ligand_chain]])

#coord1=np.array([atom.coord for atom in chain_ref[receptor_chain]])
#coord2=np.array([atom.coord for atom in chain_sample[receptor_chain]])
sup=SVDSuperimposer()
Lrms = sup._rms(coord1,coord2) #using the private _rms function which does not superimpose


#super_imposer.set_atoms(chain_ref[ligand_chain], chain_sample[ligand_chain])
#super_imposer.apply(sample_model.get_atoms())
#coord1=np.array([atom.coord for atom in chain_ref[receptor_chain]])
#coord2=np.array([atom.coord for atom in chain_sample[receptor_chain]])
#Rrms= sup._rms(coord1,coord2)
#should give same result as above line
#diff = coord1-coord2
#l = len(diff) #number of atoms
#from math import sqrt
#print sqrt(sum(sum(diff*diff))/l)
#print np.sqrt(np.sum(diff**2)/l) 

DockQ=(float(fnat) + 1/(1+(irms/1.5)*(irms/1.5)) + 1/(1+(Lrms/8.5)*(Lrms/8.5)))/3
print '*** DockQ and other docking quality measures *** '
print 'Number of equivalent residues in chain ' + chain1 + ' ' + str(len1) + ' (' + class1 + ')'
print 'Number of equivalent residues in chain ' + chain2 + ' ' + str(len2) + ' (' + class2 + ')'
print 'Fnat ' + fnat + ' ' + nat_correct + ' correct of ' + nat_total + ' native contacts'
print 'Fnonnat ' + fnonnat + ' ' + nonnat_count + ' non-native of ' + model_total + ' model contacts'
print 'iRMS ' + str(irms)
print 'LRMS ' + str(Lrms) #+ ' Ligand RMS'
#print 'RRMS ' + str(Rrms) + ' Receptor RMS'
print 'CAPRI ' + capri_class(fnat,irms,Lrms)
print 'DockQ_CAPRI ' + capri_class_DockQ(DockQ)
print 'DockQ ' + str(DockQ)

#for f in np.arange(0,1.01,0.2):
#    
#    for i in np.arange(0.5,5.5,1):
#    
#        for L in np.arange(0.5,13.5,3):
#            print str(f) + ' ' + str(i) + ' ' + str(L) + ' ' + capri_class(f,i,L)
#


# Save the aligned version of 1UBQ.pdb
#io = Bio.PDB.PDBIO()
#io.set_structure(sample_structure) 
#io.save("1UBQ_aligned.pdb")
