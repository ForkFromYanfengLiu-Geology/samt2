#!/usr/bin/env python
import sys
import os
sys.path.append(os.environ["SAMTHOME2"]+"/src/grid")	
import grid
import numpy as np
cimport numpy as np

DTYPE = np.float32
ctypedef np.float32_t DTYPE_t
ctypedef np.int_t ITYPE_t

# some constants for membership
cdef int DREIECK=0
cdef int TRAPEZ=1
cdef int LEFT=2
cdef int RIGHT=3
# fuzzy controls
cdef int FUZZYMIN=0
cdef int FUZZYMUL=1
# state of parser for read_model
cdef int INPUT=1
cdef int OUTPUT=2
cdef int RULE=3

cdef class member:
    """ Central class for Pyfuzzy to implement the membership functions:
        left, triangular,trapeze,right
        has a flag
        has a name
    """
    cdef float lu
    cdef float lo
    cdef float ro
    cdef float ru
    cdef int    flag 
    cdef char* name
    def __init__(self,name, flag1, para):
        self.name=name
        if(flag1==LEFT):
            self.lu=-9999
            self.lo=-9999
            self.ro=para[0]
            self.ru=para[1]
            self.flag=LEFT
            return
        if(flag1==RIGHT):
            self.lu=para[0]
            self.lo=para[1]
            self.ro=-9999
            self.ru=-9999
            self.flag=RIGHT
            return
        if(flag1==TRAPEZ):
            if(para[0]>para[1] or para[1]>para[2] or para[2]>para[3]):
                print "error in member!"
                print "x1=", para[0], " x2=", para[1], " x3=", para[2],
                print " x4=", para[3], "not x1>x2>x3>x4"
                sys.exit()
            self.lu=para[0]
            self.lo=para[1]
            self.ro=para[2]
            self.ru=para[3]
            self.flag=TRAPEZ
            return
        if(flag1==DREIECK):
            if(para[0]>para[1] or para[1]>para[2]):
                print "error in member!"
                print "x1=", para[0], " x2=", para[1], " x3=", para[2],
                print "not x1>x2>x3"
                sys.exit()
            self.lu=para[0]
            self.lo=para[1]
            self.ro=para[1]
            self.ru=para[2]
            self.flag=DREIECK
            return
    def get_flag(self):
        return self.flag
    def get_lo(self):
        return self.lo
    def get_lu(self):
        return self.lu
    def get_ro(self):
        return self.ro
    def get_ru(self):
        return self.ru
    def get_name(self):
        return self.name
    def get(self, float x):
        if(self.flag==DREIECK):
            if(x<=self.lu):
                return 0.0
            if(x>=self.ru):
                return 0.0
            if(x>self.lu and x<=self.lo):
                return (x-self.lu)/(self.lo-self.lu)
            return (self.ru-x)/(self.ru-self.ro)
        if(self.flag==TRAPEZ):
            if(x<=self.lu):
                return 0.0
            if(x>=self.ru):
                return 0.0
            if(x>=self.lo and x<=self.ro):
                return 1.0
            if(x>self.lu and x<self.lo):
                return (x-self.lu)/(self.lo-self.lu)
            return (self.ru-x)/(self.ru-self.ro)
        if(self.flag==LEFT):
            if(x<=self.ro):
                return 1.0
            if(x>=self.ru):
                return 0.0
            return (self.ru-x)/(self.ru-self.ro)
        if(self.flag==RIGHT):
            if(x>=self.lo):
                return 1.0
            if(x<=self.lu):
                return 0.0
            return (x-self.lu)/(self.lo-self.lu)

class input:
    """ Collects the members for a input int the list member
        has the mu list for the input
        has a name
    """
    def __init__(self,name):
        self.member=[]
        self.mu=[]
        self.name=name
        m=None
    def set_member(self,name,flag,para):
        if(flag=='left'):
            mb=member(name,LEFT,para)
        if(flag=='trapez' or flag=='trapeze'):
            mb=member(name,TRAPEZ,para)
        if(flag=='triangular'):
            mb=member(name,DREIECK,para)
        if(flag=='right'):
            mb=member(name,RIGHT,para)
        self.member.append(mb)
        self.mu.append(0.0)
    def get(self,k,float x):
        return self.member[k].get(x)
    def get_name(self,int k):
        return self.member[k].get_name()
    def calc(self,float x):
        for i in range(len(self.member)):
            self.mu[i]=self.member[i].get(x)
        return
    def get_mu(self,int i):
        return self.mu[i]
    def get_len(self):
        return len(self.member)
    def get_member(self,int i):
        return self.member[i]
    def get_n(self):
        return self.name
 
cdef class output:
    """ Collects the output which are singletons
        has val
        has mu
        has name
    """
    cdef char* name
    cdef float val
    cdef float mu 
    def __init__(self,char* name, float val):
        self.name=name
        self.val=val
        self.mu=0.0
    def get_name(self):
        return self.name
    def getv(self):
        return self.val
    def setv(self,x):
        self.val=x
        return
    def getm(self):
        return self.mu
    def setm(self,x):
        self.mu=x
        return
    
cdef class rule:
    """ Evaluates a rules of the fuzzy system
        codes the inputs and outputs with int
        has a cf
    """
    cdef int a
    cdef int b
    cdef int c
    cdef int y1
    cdef float cf
    cdef int inpn 
    cdef float mu
    def __init__(self,para):
        if(len(para)==3):  # only one input
            self.a=para[0]
            self.b=0
            self.c=0
            self.y1=para[1]
            self.cf=para[2]
            self.inpn=1
        if(len(para)==4):  # two inputs
            self.a=para[0]
            self.b=para[1]
            self.c=0
            self.y1=para[2]
            self.cf=para[3]
            self.inpn=2
        if(len(para)==5):  # three inputs
            self.a=para[0]
            self.b=para[1]
            self.c=para[2]
            self.y1=para[3]
            self.cf=para[4]
            self.inpn=3
    def calc(self,inv,flag):  # inv list of inputs
        if(flag==FUZZYMUL):
            if(len(inv)==3):
                self.mu=inv[0].get_mu(self.a)*inv[1].get_mu(self.b)\
                    *inv[2].get_mu(self.c)*self.cf
                return
            if(len(inv)==2):
                self.mu=inv[0].get_mu(self.a)*inv[1].get_mu(self.b)*self.cf
                return
            if(len(inv)==1):
                self.mu=inv[0].get_mu(self.a)*self.cf
                return
        if(flag==FUZZYMIN):
            if(len(inv)==3):
                if(inv[0].get_mu(self.a)>inv[1].get_mu(self.b)):
                    self.mu=inv[1].get_mu(self.b)
                else:
                    self.mu=inv[0].get_mu(self.a)
                if(self.mu>inv[2].get_mu(self.c)):
                    self.mu=inv[2].get_mu(self.c)
                self.mu*=self.cf
                return
            if(len(inv)==2):
                if(inv[0].get_mu(self.a)>inv[1].get_mu(self.b)):
                    self.mu=inv[1].get_mu(self.b)
                else:
                    self.mu=inv[0].get_mu(self.a)
                self.mu*=self.cf
                return
            if(len(inv)==1):
                self.mu=inv[0].get_mu(self.a)*self.cf
                return
    def geto(self):
        return self.y1
    def getm(self):
        return self.mu
    def get_cf(self):
        return self.cf
    def set_cf(self, x):
        self.cf=x
        return

class fuzzy:
    """ Main class of Pyfuzzy
        operates over inputs, outputs, rules
        has list of inputs:  inputs
        has list of outputs: outputst
        has list of rules:   rules
    """
    def __init__(self,flag=FUZZYMUL):
        self.flag=flag
        self.inputs=[]       # store the input
        self.outputs=[]      # store the outputs
        self.rules=[]        # store the ruels
        return
    def add_input(self,inp):
        self.inputs.append(inp)
        return
    def get_number_of_inputs(self):
        return len(self.inputs)
    def get_input_name(self,i):
        if(i<len(self.inputs)):
            return self.inputs[i].name
        return None
    def get_min_input(self,i):
        if(i>=len(self.inputs)):
            return None
        lo=self.inputs[i].member[0].get_lo()
        if(lo!=-9999):
            return lo
        return self.inputs[i].member[0].get_ro()
    def get_max_input(self,i):
        if(i>=len(self.inputs)):
            return None
        sel=len(self.inputs[i].member)
        ro=self.inputs[i].member[sel-1].get_ro()
        if(ro!=-9999):
            return ro
        return self.inputs[i].member[sel-1].get_lo()
    def get_output_name(self):
        return 'Output'
    def add_output(self,out):
        self.outputs.append(out)
        return
    def add_rule(self,rule):
        self.rules.append(rule)
        return
    def set_flag(self,flag):
        self.flag=flag
        return
    def get_len_output(self):
        return len(self.outputs)
    def set_output(self,i,val):
        if(len(self.outputs)>i):
            self.outputs[i]=val
            return
    def get_output(self,i):
        return self.outputs[i].getv()
    def calc1(self,float x):
        cdef float su1=0.0
        cdef float tmu=0.0
        cdef int i
        self.inputs[0].calc(x)   # calc the membership of input 1
        for i in range(len(self.rules)): # calc the membership of all rules
            self.rules[i].calc(self.inputs,self.flag)
        for i in range(len(self.rules)): # set the membership to the outputs
            if(self.outputs[self.rules[i].geto()].getm()<self.rules[i].getm()):
                self.outputs[self.rules[i].geto()].setm(self.rules[i].getm())
        for i in range(len(self.outputs)):
            if(self.outputs[i].getm()>0):
                su1+=self.outputs[i].getm()*self.outputs[i].getv()
                tmu+=self.outputs[i].getm()
                self.outputs[i].setm(0.0)
        if(tmu==0):
            return -9999
        return su1/tmu
    def calc2(self,float x1,float x2):
        cdef float su1=0.0
        cdef float tmu=0.0
        cdef int i
        self.inputs[0].calc(x1)   # calc the membership of input 1
        self.inputs[1].calc(x2)   # calc the membership of input 2
        for i in range(len(self.rules)): # calc the membership of all rules
            self.rules[i].calc(self.inputs,self.flag)
            # print i,self.rules[i].getm()
        for i in range(len(self.rules)): # set the membership to the outputs
            if(self.outputs[self.rules[i].geto()].getm()<self.rules[i].getm()):
                self.outputs[self.rules[i].geto()].setm(self.rules[i].getm())
        for i in range(len(self.outputs)):
            if(self.outputs[i].getm()>0):
                su1+=self.outputs[i].getm()*self.outputs[i].getv()
                tmu+=self.outputs[i].getm()
                self.outputs[i].setm(0.0)
        if(tmu==0):
            return -9999
        return su1/tmu
    def calc3(self,float x1,float x2,float x3):
        cdef float su1=0.0
        cdef float tmu=0.0
        cdef int i
        self.inputs[0].calc(x1)   # calc the membership of input 1
        self.inputs[1].calc(x2)   # calc the membership of input 2
        self.inputs[2].calc(x3)   # calc the membership of input 3
        for i in range(len(self.rules)): # calc the membership of all rules
            self.rules[i].calc(self.inputs,self.flag)
        for i in range(len(self.rules)): # set the membership to the outputs
            if(self.outputs[self.rules[i].geto()].getm()<self.rules[i].getm()):
                self.outputs[self.rules[i].geto()].setm(self.rules[i].getm())
        for i in range(len(self.outputs)):
            if(self.outputs[i].getm()>0):
                su1+=self.outputs[i].getm()*self.outputs[i].getv()
                tmu+=self.outputs[i].getm()
                self.outputs[i].setm(0.0)
        if(tmu==0):
            return -9999
        return su1/tmu
 
    def grid_calc1(self, g1):
        cdef int i,j
        cdef np.ndarray[DTYPE_t,ndim=2] mat1=g1.get_matp()
        cdef np.ndarray[DTYPE_t,ndim=2] matx=g1.get_matc()
        cdef int ii,jj
        (ii,jj)=g1.size()
        for i in range(ii):
            for j in range(jj):
                if(int(mat1[i,j])!=g1.get_nodata()):
                    matx[i,j]=self.calc1(mat1[i,j])
        gx=grid.grid()
        (nrows,ncols,x,y,csize,nodata)=g1.get_header()
        gx.set_header(nrows,ncols,x,y,csize,nodata)
        gx.set_mat(matx)
        return gx
    def grid_calc2(self, g1,g2):
        cdef int i,j
        cdef np.ndarray[DTYPE_t,ndim=2] mat1=g1.get_matp()
        cdef np.ndarray[DTYPE_t,ndim=2] mat2=g2.get_matp()
        cdef np.ndarray[DTYPE_t,ndim=2] matx=g1.get_matc()
        cdef int ii1,jj1, ii2,jj2
        (ii1,jj1)=g1.size()
        (ii2,jj2)=g2.size()
        if(ii1!=ii2 or jj1!=jj2):
            return None
        for i in range(ii1):
            for j in range(jj1):
                if(int(mat1[i,j])!=g1.get_nodata() and
                   int(mat2[i,j])!=g2.get_nodata()):
                    matx[i,j]=self.calc2(mat1[i,j],mat2[i,j])
        gx=grid.grid()
        (nrows,ncols,x,y,csize,nodata)=g1.get_header()
        gx.set_header(nrows,ncols,x,y,csize,nodata)
        gx.set_mat(matx)
        return gx
    def grid_calc3(self, g1,g2,g3):
        cdef int i,j
        cdef np.ndarray[DTYPE_t,ndim=2] mat1=g1.get_matp()
        cdef np.ndarray[DTYPE_t,ndim=2] mat2=g2.get_matp()
        cdef np.ndarray[DTYPE_t,ndim=2] mat3=g3.get_matp()
        cdef np.ndarray[DTYPE_t,ndim=2] matx=g1.get_matc()
        cdef int ii1,jj1, ii2,jj2,ii3,jj3
        (ii1,jj1)=g1.size()
        (ii2,jj2)=g2.size()
        (ii3,jj3)=g3.size()
        if(ii1!=ii2 or jj1!=jj2 or ii1!=ii3 or jj1!=jj3):
            return None
        for i in range(ii1):
            for j in range(jj1):
                if(int(mat1[i,j])!=g1.get_nodata() and
                   int(mat2[i,j])!=g2.get_nodata() and
                   int(mat3[i,j])!=g3.get_nodata()):
                    matx[i,j]=self.calc3(mat1[i,j],mat2[i,j],mat3[i,j])
        gx=grid.grid()
        (nrows,ncols,x,y,csize,nodata)=g1.get_header()
        gx.set_header(nrows,ncols,x,y,csize,nodata)
        gx.set_mat(matx)
        return gx


def read_model(modelname, DEBUG=0):
    f1=fuzzy()
    f = open(modelname, 'r')
    s=f.readline().rstrip()
    line=1
    sl=s.rsplit(' ')
    if(sl[0]!='input'):
        print "error in line:",line, 
        print "file should start with input"
        sys.exit()
    inputname=sl[1]
    members=int(sl[2])
    state=INPUT
    if(DEBUG==1):
        print line, inputname,members
    while(state==INPUT):
        ip=input(inputname)
        for i in range(members):  # collect members
            s=f.readline().rstrip()
            sl=s.rsplit(' ')
            line+=1
            mname=sl[1]
            mtag=sl[2]
            if(DEBUG==1):
                print line, 'member',mname,mtag
            s=f.readline().rstrip()
            line+=1
            sl=s.rsplit(' ')
            para=[]
            for i in sl:
                para.append(float(i))
            if(DEBUG==1):
                print line, para
            ip.set_member(mname,mtag,para)
        f1.add_input(ip)  # store the input in the fuzzy
        s=f.readline().rstrip()
        sl=s.rsplit(' ')
        line+=1
        inputname=sl[1]
        members=int(sl[2])
        if(DEBUG==1):
            print line,inputname,members
        if(sl[0]!='input'):
            state=OUTPUT
            oname=sl[1]
            omembers=int(sl[2])
    # new state OUTPUT must follow state INPUT
    for i in range(omembers):
        s=f.readline().rstrip()
        sl=s.rsplit(' ')
        line+=1
        oname=sl[1]
        oval=float(sl[2])
        if(DEBUG==1):
            print line, oname,oval
        out=output(oname,oval)
        f1.add_output(out)
    state=RULE  # state RULE must follow n outputs
    s=f.readline().rstrip()
    sl=s.rsplit(' ')
    line+=1
    rulenumbers=int(sl[1])
    if(DEBUG==1):
        print line,'rules:',rulenumbers
    for i in range(rulenumbers):
        s=f.readline().rstrip()
        sl=s.rsplit(' ')
        line+=1
        para=[]
        for i in sl:
            para.append(int(i))
        if(DEBUG==1):
            print line, para
        rulex=rule(para)
        f1.add_rule(rulex)
    f.close()
    return f1

