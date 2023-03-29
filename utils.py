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

        verbs=get_identified_verbs(pred)
       

        if v not in verbs: #IF verb is not found in s1 but is found in 2 is correct!
            fails+=1
            print(f"Failed for: {s} did not detect {v}\n")
            continue
     
    return (fails)/len(data)*100
