#!/usr/bin/python2.7

# query.py implements flow filtering and data selection functions
#
# see the "usage" function for instructions
#

import sys, json, operator
from optparse import OptionParser
from pprint import pprint
from math import sqrt, log
                    
class flowstats:
   def __init__(self):
      self.numbytes = 0
      self.num_msg = 0
      self.numflows = 0
      self.inbytes = 0
      self.outbytes = 0
      self.inmsg = 0
      self.outmsg = 0
      self.inbytesSq = 0
      self.outbytesSq = 0
      self.numbytesSq = 0
      self.lengths = {}
      self.times = {}
      self.rle_lengths = {}

   def observe(self, numbytes, direction, time):
      self.numbytes += numbytes
      self.numbytesSq += numbytes * numbytes
      self.num_msg += 1
      if direction == ">":
         self.outbytes += numbytes
         self.outbytesSq += numbytes * numbytes
         self.outmsg += 1
      else:
         self.inbytes += numbytes
         self.inbytesSq += numbytes * numbytes
         self.inmsg += 1
      if numbytes not in self.lengths:
         self.lengths[numbytes] = 1
      else:
         self.lengths[numbytes] = self.lengths[numbytes] + 1
      if time not in self.times:
         self.times[time] = 1
      else:
         self.times[time] = self.times[time] + 1

   def print_lengths(self):
      for x in self.lengths:
        print str(self.lengths[x]) + "\t" + str(x)
      # for x in self.rle_lengths:
      #   print str(self.rle_lengths[x]) + "\t" + str(x)

   def print_times(self):
      for x in self.times:
        print str(self.times[x]) + "\t" + str(x)
      # for x in self.rle_lengths:
      #   print str(self.rle_lengths[x]) + "\t" + str(x)

   def printflowstats(self):
      print "flows:      " + '%5s' % str(self.numflows)
      print "messages:   " + '%5s' % str(self.num_msg)
      print "bytes:      " + '%5s' % str(self.numbytes)
      print "> messages: " + '%5s' % str(self.outmsg)
      print "> bytes:    " + '%5s' % str(self.outbytes)
      print "< messages: " + '%5s' % str(self.inmsg)
      print "< bytes:    " + '%5s' % str(self.inbytes)
      if self.numflows > 0:
         amf = float(self.num_msg)/float(self.numflows)
         print "messages per flow:    " + '%5s' % str(amf)
         afs = float(self.numbytes)/float(self.numflows)
         print "bytes per flow:       " + '%5s' % str(afs) 
         amf = float(self.outmsg)/float(self.numflows)
         print "outbound messages per flow: " + '%5s' % str(amf)
         amf = float(self.inmsg)/float(self.numflows)
         print "inbound messages per flow:  " + '%5s' % str(amf)
      if self.num_msg > 1:
         ads = float(self.numbytes)/float(self.num_msg)
         print "average message size: " + '%5s' % str(ads)
         vms = (float(self.numbytesSq) - float(self.numbytes * self.numbytes)/float(self.num_msg))/float(self.num_msg - 1)
         print "std dev message size: " + '%5s' % str(sqrt(vms))
      if self.inmsg > 1:
         ads = float(self.inbytes)/float(self.inmsg)
         print "average inbound message size: " + '%5s' % str(ads)
         vms = (float(self.inbytesSq) - float(self.inbytes * self.inbytes)/float(self.inmsg))/float(self.inmsg - 1)
         print "std dev inbound message size: " + '%5s' % str(sqrt(vms))
      if self.outmsg > 1:
         ads = float(self.outbytes)/float(self.outmsg)
         print "average outbound message size: " + '%5s' % str(ads)
         vms = (float(self.outbytesSq) - float(self.outbytes * self.outbytes)/float(self.outmsg))/float(self.outmsg - 1)
         print "std dev outbound message size: " + '%5s' % str(sqrt(vms))
      


class filter:
   def __init__(self):
      self.filters = [ ]
  
   def match(self, flow):
      # by default, match everything
      if not self.filters:     
         return True
      # match any filter
      for f in self.filters:
         if f.match(flow):
            return True

   def addFilter(self, f):
      self.filters.append(f)

class conjunctionFilter(filter):

   def match(self, flow):
      # by default, match nothing
      if not self.filters:     
         return False
      # match all filter
      tval = True
      for f in self.filters:
         tval = tval and f.match(flow)
      return tval

def entropy(bd):
   if type(bd) is not list:
      print "error: wrong type argument to entropy function"
      sys.exit()
   sum = 0.0
   e = 0.0
   for x in bd:
      sum = sum + x
   if sum == 0.0:
      return 0.0
   for x in bd:
      p = x / sum
      if p > 0:
         e = e - p * log(p)
   return e / log(2.0)

def collision(bd):
   if type(bd) is not list:
      print "error: wrong type argument to collision entropy function"
      sys.exit()
   total = 0.0
   e = 0.0
   for x in bd:
      total = total + x
   if total == 0.0:
      return 0.0
   for x in bd:
      p = x / total
      e = e + (p * p)
   if e == 0.0:
      e = 0.0
   else:
      e = - log(e) / log(2.0)
   return e

def minentropy(bd):
   if type(bd) is not list:
      print "error: wrong type argument to collision entropy function"
      sys.exit()
   total = 0.0
   e = 0.0
   for x in bd:
      total = total + x
   if total == 0.0:
      return 0.0
   for x in bd:
      if x > e:
         e = x
   if e == 0.0:
      e = 0.0
   else:
      e = - log(e / total) / log(2.0)
   return e

def gini(bd):
   if type(bd) is not list:
      print "error: wrong type argument to gini function"
      sys.exit()
   total = 0.0
   for x in bd:
      total = total + x
   if total == 0.0:
      return 0.0

   bd.sort()   
   n = len(bd)
   for i in range(n):
      bd[i] = bd[i] / total
   print "bd: " + str(bd)
   e = 0.0
   for i in range(n):
      e = (n - i) * bd[i]
   e = 1 + (- 2 * e)/float(n)
   print "gini: " + str(e)
   return e

def identity(x):
   return x

def alwaysTrue(x,y):
   return True

class matchType:
   base = 0
   list_any = 1
   list_all = 2

class flowFilter:

   def selectField(self, a):
      if self.field2 is None:
         return a
      else:
         if self.field2 in a:
            return a[self.field2]
         return None

   def __init__(self, string):
      self.func = identity
      
      if string is None:
         self.matchAll = True
         return
      else:
         self.matchAll = False

      # remove whitespace
      string = string.replace(" ", "")         

      for op in [ '=', '>', '<' ]: 
         if op in string:
            (self.field, self.value) = string.split(op, 2)

            # look for functions
            if '(' in self.field:
               funcname, argument = self.field.split('(')
               if ')' in argument:
                  self.field = argument.split(')')[0]
                  if funcname == "entropy":
                     self.func = entropy
                  elif funcname == "collision":
                     self.func = collision
                  elif funcname == "minentropy":
                     self.func = minentropy
                  elif funcname == "gini":
                     self.func = gini
                  else:
                     print "error: unrecognized function " + funcname
                     sys.exit()
               else:
                  print "error: could not parse command " + str(string)
                  sys.exit()
      
            # arrays are notated array[all] or array[any]
            if "[all]" in self.field:
               self.field = self.field.replace("[all]", "")
               self.type = matchType.list_all
            elif "[any]" in self.field:
               self.field = self.field.replace("[any]", "")
               self.type = matchType.list_any
            else:
               self.type = matchType.base
            # print self.field

            # subfields are notated "flow.subfield"
            if '.' in self.field:
               (self.field, self.field2) = self.field.split(".", 2)
            else:
               self.field2 = None
         
            if self.value.isdigit():
               self.value = int(self.value)

            if op == '=':
               if self.value is '*':
                  self.operator = alwaysTrue
               else:
                  self.operator = operator.eq 
            if op == '<':
               self.operator = operator.lt 
            if op == '>':
               self.operator = operator.gt 
            # print "filter: " + self.field + " " + str(self.operator) + " " + str(self.value)



   def matchElement(self, filter):
      # print "this is my filter: " + str(filter)
      # print "type: " + str(self.type) + " : " + str(matchType.list_all)
      if self.type is matchType.base:
         # print self.func(self.selectField(filter)),
         # print self.operator,
         # print self.value,
         # print type(self.value),
         # print " = ",
         # print self.operator(self.func(self.selectField(filter)), float(self.value))
         # print "------"
         if self.operator(self.func(self.selectField(filter)), float(self.value)):
            return True
         else:
            return False
      elif self.type is matchType.list_all:
         tval = True
         if not filter:
            return False
         for x in filter:
            tval = tval and self.operator(self.selectField(x), self.value)
         return tval
      elif self.type is matchType.list_any:
         if not filter:
            return False
         for x in filter:
            if self.operator(self.selectField(x), self.value):
               return True
         return False

   def match(self, flow):
      if self.matchAll is True:
         return True         
      if self.field in flow:
         return self.matchElement(flow[self.field])

import string

class noTranslation():
   def __init__(self):
      pass

   def translate(self, s, val):
      return val

class translator():
   def __init__(self):
      try:
         self.initialize()
      except:
         print "error: could not initialize translator (check for missing data files)"
         sys.exit()

   def initialize(self):
      self.d = {}
      with open("saltUI/ciphersuites.txt") as f:
         for line in f:
            (key, val, sec) = line.split()
            self.d[key] = val + " (" + sec + ")"
      
      self.pr = {
         6: "TCP",
         17: "UDP"
         }
      with open("data/ip.txt") as f:
         for line in f:
            (key, val) = line.split()
            self.pr[key] = val

      self.ports = {}
      with open("data/ports.txt") as f:
         for line in f:
            try:
               (val, key) = line.split()
               if '-' in str(key):
                  start, stop = str(key).split('-')
                  for a in range(int(start), int(stop)):
                     self.ports[a] = string.upper(val)
               else:
                  key = int(key)
                  self.ports[key] = string.upper(val)
            except:
               pass
               # print "could not parse line " + line


   def translate(self, s, val):
      if s is "scs" or s is "cs":
         return self.d.setdefault(val, "unknown")
      elif s is "pr":
         return self.pr.setdefault(val, "unknown")
      elif s is "dp" or s is "sp":
         z = self.ports.setdefault(val, None)
         if z is None:
            return val
         else:
            return z
      else:
         return val

def elementPrint(f, *elements):
   printComma = True
   for s in elements:
      if s is "START":
         printComma = False
      if (s) in f:
         if printComma:
            print ","
         else:
            printComma = True
         val = t.translate(s, f[s])
         print "         \"" + s + "\": ",
         if type(val) is int or type(val) is float:
            print str(val),
         else:
            print "\"" + str(val) + "\"",

def listPrint(f, listname, itemsPerLine=16):
   first = True
   count = 0
   if listname in f:
      print ","
      print "         \"" + listname + "\": [",
      for x in f[listname]:
         if not first:
            print ",",
         else:
            first = False
         if count % itemsPerLine == 0:
            print
            print "         ",
         val = t.translate(listname, x)
         print '%4s' % str(val),
         count = count + 1
      print
      print "          ]",

def listPrintObject(f, listname, *elements):
   first = True
   if listname in f:
      print ","
      print "         \"" + listname + "\": ["
      for x in f[listname]:
         if not first:
            print ","
         else:
            first = False
         print "            {",
         objFirst = True
         for s in elements:
            if (s) in x:
               if not objFirst:
                  print ",",
               else:
                  objFirst = False
               print " \"" + s + "\": ",
               if type(x[s]) is int or type(x[s]) is float:
                  print str(x[s]),
               else:
                  print "\"" + str(x[s]) + "\"",
         print "}",
      if f[listname]:
         print
      print "          ]",

def objectPrint(f, objname):
   first = True
   if objname in f:
      print ","
      print "         \"" + objname + "\": {"
      for x in f[objname]:
         if not first:
            print ","
         else:
            first = False
         print "            \"" + str(x) + "\": \"" + str(f[objname][x]) + "\"",
      print
      print "          }",

def flowPrint(f):
      print "   {"
      # print json.dumps(f, indent=3),
      # OLD: print "      \"flow\": {"
      elementPrint(f, "START", "sa", "da", "pr", "sp", "dp", "ob", "op", "ib", "ip", "ts", "te", "ottl", "ittl")
      listPrintObject(f, "packets", "b", "dir", "ipt")
      listPrint(f, "bd")
      listPrint(f, "compact_bd")
      elementPrint(f, "bd_mean", "bd_std", "be", "tbe", "i_probable_os", "o_probable_os")
      listPrintObject(f, "dns", "qn", "rn")
      elementPrint(f,  )
      listPrint(f, "cs", 1)
      elementPrint(f, "scs")
      objectPrint(f, "tls") # , "tls_iv", "tls_ov", "tls_orandom", "tls_irandom", "tls_osid", "tls_isid", "srlt")
      objectPrint(f, "ihttp")
      objectPrint(f, "ohttp")
      # OLD: print "\n      }"
      print "\n   }"


class flowProcessor:
   def __init__(self):
      self.firstFlow = 1

   def processFlow(self, flow):
      # OLD: if not self.firstFlow:
      # OLD:    print ","
      # OLD: else:
      # OLD:    self.firstFlow = 0
         # OLD: print "\"appflows\": ["
      flowPrint(flow)

   def processMetadata(self, metadata):
      # OLD: print "\"metadata\": ", 
      print json.dumps(metadata, indent=3),
      # OLD: print ","

   def preProcess(self):    
      pass
      # OLD: print "{"

   def postProcess(self):    
      if self.firstFlow:
         self.firstFlow = 0
         # OLD: print "\"appflows\": ["
      # OLD: print "]"
      # OLD: print "}"

import time

def flowSummaryPrint(f):
      print "%32s" % str(f["sa"]), 
      print "%32s" % str(f["da"]),
      print "%4s" % str(f["pr"]),
      print "%6s" % str(f["sp"]),
      print "%6s" % str(f["dp"]),
      print "%6s" % str(f["ob"]),
      print "%6s" % str(f["op"]),
      if "ib" in f:
         print "%6s" % str(f["ib"]),
         print "%6s" % str(f["ip"]),
      else:
         print "             ",
      print time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(f["ts"])) + " ",
      print round(f["te"] - f["ts"], 3)
      # print time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(f["te"]))
      # print "%14s" % str(f["ts"]) + " ",
      # print "%14s" % str(f["te"])

class flowSummaryProcessor(flowProcessor):
     def processFlow(self, flow):
        flowSummaryPrint(flow)

     def processMetadata(self, metadata):
        pass
     
     def preProcess(self):    
        print "%32s" % "source address", 
        print "%32s" % "destination address",
        print "%4s" %  "prot",
        print "%6s" % "sport",
        print "%6s" % "dport",
        print "%6s" % "obytes",
        print "%6s" % "opkts",
        print "%6s" % "ibytes",
        print "%6s" % "ipkts",
        print "%19s" % "date     time",
        print "%8s" % "seconds"
     
     def postProcess(self):    
        pass


def printable(s):
   if not s.isdigit():
      return "\"" + s + "\""
   else:
      return str(s)

class printSelectedElements:
   def __init__(self, field):
      self.func = identity
      self.funcname = None
      self.firstFlow = True
      self.field = field.replace(" ", "") # no whitespace
      if '.' in self.field:
         (self.field, self.field2) = self.field.split(".", 2)
         self.depth = 2
      else:
         self.depth = 1

      # look for functions
      if '(' in self.field:
         self.funcname, argument = self.field.split('(')
         if ')' in argument:
            self.field = argument.split(')')[0]
            if self.funcname == "entropy":
               self.func = entropy
            elif self.funcname == "collision":
               self.func = collision
            elif self.funcname == "minentropy":
               self.func = minentropy
            elif self.funcname == "gini":
               self.func = gini
            else:
               print "error: unrecognized function " + funcname
               sys.exit()
         else:
            print "error: could not parse command " + str(string)
            sys.exit()


   def processFlow(self, flow, first):
      # print "   {"
      # print "      \"flow\": ",
      # print json.dumps(flow, indent=3),

      if self.field in flow:
         filter = flow[self.field]
         if self.depth is 1:
            if self.funcname is not None:
               name = self.funcname + "(" + self.field + ")"
            else:
               name = self.field
            if first:
               first = False
               if not self.firstFlow:
                  print ",",
               else:
                  self.firstFlow = False
               print  "\n\t{ ",
            else:
               print ", ",
            print "\"" + name + "\": " + str(self.func(filter)), 
         else:
            if type(filter) is list:
               for a in filter:
                  if self.field2 in a:
                     filter2 = a[self.field2]
                     print "\"" + str(self.field2) + "\": " + printable(filter2),
                     if first:
                        first = False
                        if not self.firstFlow:
                           print ",",
                        else:
                           self.firstFlow = False
                        print  "\n\t{ ",
                     else:
                        print ", ",
                     print "\"" + str(self.field2) + "\": " + printable(filter2),
            else:
               if self.field2 in filter:
                  filter2 = filter[self.field2]
                  if first:
                     first = False
                     if not self.firstFlow:
                        print ",",
                     else:
                        self.firstFlow = False
                     print  "\n\t{ ",
                  print "\"" + str(self.field2) + "\": " + str(filter2),
      # print "   }",
      return first

   def processMetadata(self, metadata):
      pass

   def preProcess(self):    
      print "{"
      print "\"" + str(self.field) + "\": ["

   def postProcess(self):    
      print
      print "   ]"
      print "}"


class printMultipleElements():
   def __init__(self, name):
      self.array = []
      self.field = name
      self.firstFlow = True

   def addElement(self, x):
      self.array.append(x)

   def processFlow(self, flow):
      first = True
      for x in self.array:
         first = x.processFlow(flow, first)
      if not first:
         print "}",

   def preProcess(self):    
      print "{"
      print "\"" + str(self.field) + "\": [",

   def postProcess(self):    
      print
      print "   ]"
      print "}"

   def processMetadata(self, metadata):    
      pass


class flowStatsPrinter:
   def __init__(self):
      self.flowdict = {}
      self.flowtotal = flowstats()      

   def processFlow(self, flow):
      #
      # keep separate statistics for each destination port
      dp = flow["dp"]
      if dp not in self.flowdict:
         fs = flowstats()
         self.flowdict[dp] = fs
      else:
         fs = self.flowdict[dp]

      fs.numflows += 1
      self.flowtotal.numflows += 1
      for x in flow['packets']:
         fs.observe(x["b"], x["dir"], x["ipt"])
         self.flowtotal.observe(x["b"], x["dir"], x["ipt"])      

   def processMetadata(self, metadata):
      pass

   def preProcess(self):    
      print

   def postProcess(self):      
      # for fs in self.flowdict:
      #   print "flow stats for dp=" + str(fs)
      #   self.flowdict[fs].printflowstats()
      #   print 
      print "total flow stats"
      self.flowtotal.printflowstats()
      # self.flowtotal.print_lengths()
      # self.flowtotal.print_times()


def description(t):
   if t is str:
      return "string"
   if t is int:
      return "int"
   if t is list:
      return "list"
   if t is object:
      return "object"
   if t is float:
      return "float"
   return "unknown"

class printSchema:
   def __init__(self):
      self.firstFlow = 1
      self.indentation = ""
      self.schema = {}

   def processDatum(self, x, y):
      t = type(y)
      if t is dict:
         print "processing object: " + str(y)
         tmp = self.indentation
         self.indentation = self.indentation + "\t"
         self.processFlow(y)
         self.indentation = tmp
         self.schema[x] = "flow.object" + str(x) + '\t' 
      elif t is list:
         print "processing list: " + str(y)
         tmp = self.indentation
         self.indentation = self.indentation + "\t"
         # self.processFlow((y)[1])
         self.indentation = tmp
      else:
         print self.indentation + "flow." + str(x) + '\t' + description(t)
         self.schema[x] = self.indentation + "flow." + str(x) + '\t' + description(t)
      

   def processFlow(self, flow):
      print "got flow"
      for x in flow:
         self.processDatum(x, flow[x])

   def printSchema(self, schema):
      for x in schema:
         print schema[x] + " " + str(type(schema[x]))
         if type(schema[x]) is dict:
            print "printing dictionary"
            self.printSchema(x)

   def preProcess(self):    
      pass

   def postProcess(self):    
      print "schema: "
      # print self.schema
      self.printSchema(self.schema)
      
   def processMetadata(self, x):
      pass

def processFileOld(f, ff, fp):
   global flowdict, flowtotal
   json_data=open(f)
   data = json.load(json_data)

   if "metadata" in data:
      fp.processMetadata(data["metadata"])

   for flow in data["appflows"]:
      if ff.match(flow["flow"]):
         fp.processFlow(flow["flow"])
   json_data.close()

def processLine(line):
   if line.strip == '{' or 'metadata' in line:
      self.legacy_format = True
      print "warning: legacy JSON format"
      return
   try:
      tmp = json.loads(line)
      if 'version' not in tmp:
         if ff.match(tmp):
            fp.processFlow(tmp)
   except:
      pass

import gzip

def processFile(f, ff, fp):
   if f is '-':
      for line in sys.stdin:
         processLine(line)
   else:
      if ".gz" in f:
         with gzip.open(f,'r') as jsonobjects:
            for line in jsonobjects:
               processLine(line)
      else:
         with open(f,'r') as jsonobjects:
            for line in jsonobjects:
               processLine(line)



def usage():
   print
   print "EXAMPLE"
   print "./query.py sample.json --where \" packets[any].b = 478 & pr = 6\" --select dp"
   print
   print "FILTER examples:"
   print "  dp=443"
   print "  \"dp > 1024\""
   print "  \"sa = 10.0.0.1\""
   print "  \"pr = 17\""
   print "  \"bd[all] > 10\""
   print "  \"bd[any] > 10\""
   print "  \"packets[any].b = 41 & ip = 2\""
   print "  \"packets[all].ipt < 5 & dp = 80\""
   print "  \"entropy(bd) > 7.0\""
   print "  \"collision(bd) > 7.0\""
   print "  \"minentropy(bd) > 7.0\""
   print
   print "SELECTION examples:"
   print "  dp"
   print "  sa"
   print "  ohttp.uri"
   print "  packets"
   print "  packets.ipt"
   print "  \"entropy(bd)\""
   print "  \"collision(bd)\""
   print "  \"minentropy(bd)\""

#
# main function 
#
if __name__=='__main__':

   parser = OptionParser()
   parser.set_description("filter JSON flow data and print out matching flows, selected fields, or stats")
   parser.add_option("--where", dest="filter", help="filter flows")
   parser.add_option("--select", dest="selection", help="select field to output")
   parser.add_option("--stats", action="store_true", help="print out statistics")
   parser.add_option("--summary", action='store_true', dest="summary", help="print single line per flow ")
   parser.add_option("--translate", action='store_true', dest="translate", help="translate numbers to acronyms ")
   parser.add_option("--schema", action='store_true', dest="schema", help="print out schema")

   # check args
   if len(sys.argv) < 2:
      parser.print_help()
      usage()
      sys.exit()

   (opts, args) = parser.parse_args()

   if opts.translate is True:
      t = translator()
   else:
      t = noTranslation()

   if opts.selection is not None:
      # fp = printSelectedElements(opts.selection)
      fp = printMultipleElements("name")
      for z in opts.selection.split(','):
         fp.addElement(printSelectedElements(z))
   else:
      if opts.schema is True:
         fp = printSchema()
      elif opts.stats is True:
         fp = flowStatsPrinter()
      elif opts.summary is True:
         fp = flowSummaryProcessor()
      else:
         fp = flowProcessor()      

   ff = filter()
   if opts.filter:
      for z in opts.filter.split('|'):
         # print "disjunction: " + str(z)
         if '&' in z:
            conjf = conjunctionFilter()
            for conj in z.split('&'):
               # print "conjunction: " + str(conj)
               conjf.addFilter(flowFilter(conj))
            ff.addFilter(conjf)
         else:
            ff.addFilter(flowFilter(z))

   if not args:
      parser.print_help()
      usage()
      sys.exit()

   # process all files, with preamble and postable
   #
   fp.preProcess()
   for x in args:
      try:
         processFile(x, ff, fp)
      except KeyboardInterrupt:
         # quit
         sys.exit()      
      # except:
         # silently ignore failures, for now
      #   pass
   fp.postProcess()




