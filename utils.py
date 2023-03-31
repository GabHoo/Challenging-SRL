import re
import json
def get_identified_verbs(pred): 
    """This function returns a list of verbs that are identified in the prediction
    :pred is the output of predictor.predict()
    """
    verbs=[x['verb'] for x in pred['verbs']]
    return verbs

def evaluate_PI_Polysem_DIR(predictor,data):
    """
    This function return the failure rates percentage on a test set.
    :predictor is predictor object
    :data is dictionary in the shape {'verb':[s1,s2]} 
    WHERE s1 contains the wordd as a noun/adjective, S2 as verb

    returns failure rate
    """
    correct=0
    for v in data:
        s1,s2=data[v] 
        
        pred1=predictor.predict(s1)
        pred2=predictor.predict(s2)

        v1=get_identified_verbs(pred1)
        v2=get_identified_verbs(pred2)

        if v not in v1 and v in v2: #IF verb is not found in s1 but is found in 2 is correct!
            correct+=1
            continue
        else:
            print(f"Failed for: [{s1}],[{s2}]. {v} in both did NOT chage the predicate identification")
            print(v1,v2)
            #print(f"{pred1['verbs']=} \n{pred2['verbs']=}")
            print("\n")
    return (len(data)-correct)/len(data)*100

def evaluate_PI_Contractions_INV(predictor,data):             
    """
    This function returns a failure rate (percentage) that represents how many coupled sentnece 
    presents inconcitency in their tags of a contracted predicate. The idea is that a predictor should be able to identify a verb even if varieted.
    Matching is TAG BASED: The models must have predicted a verb in the given position (inflected verb), if not is a failure.

    :predictor
    :data is a list of tupleslists where the nested lists are couple of sentence to be compared

    returns a failure rate
    """

    data=[(i,v[0],v[1]) for i,v in data.items()] #NECESSARY CONVERSION FROM FILE, ugly i know
    
    fail=0
    
    for s in data:
        s1,s2,i=s
        pred1=predictor.predict(s1)
        pred2=predictor.predict(s2)

        v1=get_identified_verbs(pred1)
        v2=get_identified_verbs(pred2)

        if len(v1)!=len(v2):
            print(f"Failure in {s1} | {s2}")
            print(f"Different number of verbs found: {v1=} against {v2=}")
            fail+=1
            continue

                
        for v1,v2 in zip(pred1['verbs'],pred2['verbs']):
            if v1['verb']!=v2['verb']: #we only compare the verbs that are not matching exactly (aka the contracted vs original)
                if v1['tags'][i]!='B-V' or v2['tags'][i]!='B-V': #And if one of them is not found to be a verb, test fails
                    fail+=1
                    print(f"Failure in {s1} | {s2}")
                    print(f"The alteration of verb {v1['verb']}/{v2['verb']} lead to a different labeling:\n")
                    print(v1)
                    print(v2)
                    break   
    
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