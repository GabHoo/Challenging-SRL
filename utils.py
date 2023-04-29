import re
import json


def get_identified_verbs(pred): 
    """This function returns a list of verbs that are identified in the prediction
    :pred is the output of predictor.predict()
    """
    verbs=[x['verb'] for x in pred['verbs']]
    return verbs

def evaluate_PI_Polysem_DIR(predictor,data,verbose=True):
    """
    This function return the failure rates percentage on a test set.
    :predictor is predictor object
    :data is dictionary in the shape {'verb':[s1,s2]} 
    WHERE s1 contains the wordd as a noun/adjective, S2 as verb

    returns failure rate
    """
    fail=0
    for v in data:
        s1,s2=data[v] 
        
        pred1=predictor.predict(s1)
        pred2=predictor.predict(s2)

        v1=get_identified_verbs(pred1)
        v2=get_identified_verbs(pred2)

        if v in v1:#IF verb is not found in s1 but is found in 2 is correct!
            fail+=1
            if verbose:
                print(f"Failed for: {s1} ... [{v}] found as a verb ")
            continue

        if v not in v2:
            fail+=1
            if verbose:
                print(f"Failed for: {s2} ... [{v}] not found as a verb")
            continue   
        
    return fail/len(data)*100



def evaluate_PI_contractions_INV(predictor,data,verboose=True):
    """
    This function returns a failure rate (percentage) that represents how many coupled sentnece 
    presents inconcitency in their tags of a contracted predicate. The idea is that a predictor should be able to identify a verb even if varieted.
    Matching is TAG BASED: The models must have predicted a verb in the given position (inflected verb), if not is a failure.

    :predictor
    :data is a list of lists where the nested lists are couple of sentence and their index to be compared

    returns a failure rate
    """
    fail=0
    for c,i in data:
        s1,s2,index= c[0],c[1],i
        pred1=predictor.predict(s1)
        pred2=predictor.predict(s2)

        v1=get_identified_verbs(pred1)
        v2=get_identified_verbs(pred2)

        if pred1['words'][index] not in v1 and pred2['words'][index] not in v2:
            fail+=1
            if verboose:
                print(f"{pred1['words'][index]} or {pred2['words'][index]} not found as verb in {v1=} or {v2=}")

    return fail/len(data)*100



def evaluate_PI_inflections_MFT(predictor,data):
    """
    This functions tests MFT for inflected verb forms. Models needs to be able to detect them as verbs, if not, fail
    :predictor
    :data is a dict {verb:sentence}
    
    output is failure rate
    """

    fails=0
    for v in data:
        s=data[v] 
        
        pred=predictor.predict(s)
        #print(pred)

        verbs=get_identified_verbs(pred)
       

        if v not in verbs: #IF verb is not found in s1 but is found in 2 is correct!
            fails+=1
            print(f"Failed for: {s} did not detect {v}\n")
            #print(v,verbs)

            continue
     
    return (fails)/len(data)*100

def evaluate_INV_alltags(pred1,pred2,verbose=False):
  """
  This functions matches the verbs and then control the tags of the verbs in two predictions. Verbs dont have to be the same tho!
  """
  if len(pred1['verbs'])!=len(pred2['verbs']) or len(pred1['verbs'])==0 or len(pred2['verbs'])==0:
    if verbose:
        print("Not the same number of verbs identified in the sentences! Might also be 0!")
        print(pred1['words'],pred2['words'])
        print("Verbs found: ",[x['verb'] for x in pred1['verbs']],[x['verb'] for x in pred2['verbs']],"\n")
    return False

  for v in zip(pred1['verbs'],pred2['verbs']): 
      v1,v2=v      

      if v1['tags']!=v2['tags']:
        if verbose:
            print(f"missmatch in tags for verbs [{v1['verb']} and {v2['verb']}]")
            print(f"sentences: {v1['description']} and {v2['description']}")
            print(f"tags: {v1['tags']} and {v2['tags']}")
            print("\n\n")
        return False

      continue
  return True


def validate_INV_allverbs_ARGset(pred1,pred2,verbose=True):
  """
  This functions matches the verbs and check the unique set of arguments of the verb in two predictions
  """
  #assert pred1['words']==pred2['words'],f"ERROR, Comparing two different sentences"
  if len(pred1['verbs'])!=len(pred2['verbs']):
    if verbose:
      print("not the same number of verbs were found!")
      print(pred1['words'],pred2['words'])
      print([x['verb'] for x in pred1['verbs']],[x['verb'] for x in pred2['verbs']],"\n")
    return False

  for v in zip(pred1['verbs'],pred2['verbs']): 
      v1,v2=v
      
      if v1['verb']!=v2['verb']: #verbs should not change when propnouns are changing
        if verbose:
          print("missmatch in verb identification \n,v1['verb'] and v2['verb']\n")
        return False
      
      
      unique_tag1=get_unique_args(v1['tags'])

      unique_tag2=get_unique_args(v2['tags'])

      if unique_tag1!=unique_tag2:
        if verbose:
          print(f"missmatch in the arguments found tags of verb '{v1['verb']}'\n{v1['description']}\n{v2['description']}\n")
        return False

      continue
  return True

def get_unique_args(s):
  """
  Returns the unique arguments in a list of BIO tags.
  """
  return set([x[2:] for x in s if x!='O'])

def get_dict_args(description):
    """
    Returns a dictionary of the arguments found in the description of a verb
    Key is the argument, value is the span"""
    args=re.findall(r'\[.*?\]',description)#take the string with brakets (arguments and V)
    argsdict={}
    for x in args:
        l=(x[1:-1].split(":"))#split the string to get the key and value
        key=l[0]
        value=l[1].strip()
        argsdict[key]=value
    return argsdict

def get_main_verb(pred):
    max=1
    for x in pred['verbs']:
        if len(get_dict_args(x['description']))>max:
            best_verb=x
            max=len(get_dict_args(x['description']))
    return best_verb

def evaluate_INV_sameArgs(preda,predp,verbose=True):
    """
    This functions checks if the arguments of the main verb are the same in two predictions. focus on main verb.
    Crefull, it only works for sentences with one verb and where the verb is regularly reabsformed with auxiliaries
    """
        
    best_verba = get_main_verb(preda)
    best_verbp = get_main_verb(predp)

    da=get_dict_args(best_verba['description'])
    dp=get_dict_args(best_verbp['description'])

    dp.pop("V")
    da.pop("V")

    if da.keys()!=dp.keys():
        print("different arguments")
        return False
        

    for k in da.keys():

        words1 = set(da[k].lower().split())
        words2 = set(dp[k].lower().split())

        # Find the common words using the intersection method
        common_words = words1.intersection(words2)
        if (common_words):
            #print(common_words) 
            continue
        else:
            return False
    return True


def check_NER_tags(pred,golden):
    """
    Takes a list of golden tags and a prediction and returns True if the prediction is correct
    """
    v=[x['verb'] for x in pred['verbs']]
    if (v==['saw']):
        if (pred['verbs'][0]['tags']==golden):
            return True
    else:
        return False
    
def eval_NER(sentences,labels,predictor):
    fails=0
    for s in sentences:
        pred=predictor.predict(s)
        success=check_NER_tags(pred,labels)
        if not success:
            fails+=1
    return fails/len(sentences)*100
    
def find_roleset_MFT(sents,predictor,verboose=False):
    """Takes a dict where every key is the noun/adj that introduces a rolesets and value is the sentence.
        Model should detect them among the verbs list according to Propbank"""
    fail=0
    for x,s in sents.items():
        roleset=x
        pred=predictor.predict(s)
        rolesets_found=[x['verb'] for x in pred['verbs']]

        if roleset not in rolesets_found:
            
            if verboose:
                print(f"[{x}] not detected from '{s}', only {rolesets_found} were found")
            
            fail+=1

    return fail/len(sents)*100    


def eval_full_sent_BIOtags(sents,labels,predictor,verb_indx=0,verbose=True):
    """
    This function evaluates the predictor by using the BIO tags of the predictions.
    """
    fails=0
    for s in sents:
        pred = predictor.predict(s)
        if pred['verbs'][verb_indx]['tags'] != labels:
            fails+=1
            if verbose:
                print("Sentence: ",s)
                print("Predicted BIO tags: ",pred['verbs'][verb_indx]['tags'])
                print("True BIO tags: ",labels)
          
    return (fails/len(sents)*100)

def eval_full_sent_BIOtags(sents,labels,predictor,verb_indx=0,verbose=True): #verb_indx to 0 as it is often  the case that there is only one predicate
    """
    This function evaluates the predictor by using the BIO tags of the predictions.
    """
    fails=0
    for s in sents:
        #print(s)
        pred = predictor.predict(s)
        if not pred['verbs']: #no verb found
            fails+=1
            if verbose:
                print("\n FAILED FOR Sentence: ",s)
                print("no verbs found ")
            continue
            
        pred_labels=pred['verbs'][verb_indx]['tags']
   
        if pred_labels != labels: #wrong prediction
            fails+=1
            if verbose:
                print("\n FAILED FOR Sentence: ",s)
                print("Predicted BIO tags: ",pred_labels)
                print("True BIO tags: ",labels)
          
    return (fails/len(sents)*100)

def eval_full_sent_BIOtags_INV(sentences,labels1,labels2,predictor,verbose=False):
    """
    This function evaluates the performance of the model on a list of couple of sentence for INV TEST.
    :sentences is a dict where key is s1 and value is s2
    :labels1 is the list of BIO tags for the first sentence
    :labels2 is the list of BIO tags for the second sentence
    :predictor is the predictor

    returns the rate of failure
    """
   
    fails=0
    for a,p in sentences.items():
        predA=predictor.predict(a)
        predP=predictor.predict(p)
        
        if predA['verbs'][0]['tags']!=labels1 or predP['verbs'][1]['tags']!=labels2: #1 because we the auxiliary in position 0
            print("Error")
            fails+=1
            print(predA['verbs'][0]['description'],"!=",labels1)
            print(predP['verbs'][1]['description'],"!=",labels2)
                
            print("\n\n")

    return fails/len(sentences)*100   

def eval_PP_MFT(di,predictor,verbose=False):
    """This function evaluates a big datasets of known PP attachment. 
    They all refer to the noun thus the label to be predicted must be ['I-ARG1', 'I-ARG1']
    structure of the sentence is always the same. 4 words where last two is PP"""
    failure=0
    for c in di:
        pred=predictor.predict(c)
        if not pred['verbs']:
            failure+=1
            if verbose:
                print(f"verbs not found in sentence: {c}")
            continue

        pp_pred=pred['verbs'][0]['tags'][-2:]

        if pp_pred!=['I-ARG1', 'I-ARG1']:
            failure+=1
            if verbose:
                print(f"Input sentence: {c}")
                print(f"Predicted labels for PP: {pp_pred} but should have been ['I-ARG1', 'I-ARG1']")
            continue
    
    return failure/len(di)*100

def eval_PP_INV(sentences,predictor,verbose=False):
    """
    Evaluate the model on the PP attachment  based on partial pos tags. Lables given are infact only the one of the PP
    """
    failure=0
    for c in sentences:
        s1,s2=c.keys()
        pred1=predictor.predict(s1)
        pred2=predictor.predict(s2)
        labels1=c[s1]
        labels2=c[s2]
        ll1=len(labels1)
        ll2=len(labels2)
        if pred1['verbs'][0]['tags'][-ll1:]!=labels1:
            failure+=1
            if verbose:
                print(f"Input sentences: {s1}")
                print(f"Predicted labels for PP: {pred1['verbs'][0]['tags'][-ll1:]} but should have been {labels1}")
            continue
        if pred2['verbs'][0]['tags'][-ll2:]!=labels2:
            failure+=1
            if verbose:                             
                print(f"Input sentences: {s2}")
                print(f"Predicted labels for PP: {pred2['verbs'][0]['tags'][-ll2:]} but should have been {labels2}")
                      

    return failure/len(sentences)*100