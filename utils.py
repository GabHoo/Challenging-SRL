def get_identified_verbs(pred): 
    """This function returns a list of verbs that are identified in the prediction
    :pred is the output of predictor.predict()
    """
    verbs=[x['verb'] for x in pred['verbs']]
    return verbs

def evaluate_verbIdentification_DIR(predictor,data):
    """This function return the failure rates percentage on a test set.
    :predictor is predictor object
    :data is dictionary in the shape {'verb':[s1,s2]} 
    """
    correct=0
    for v in data:
        s1,s2=data[v] 
        
        pred1=predictor.predict(s1)
        pred2=predictor.predict(s2)

        v1=get_identified_verbs(pred1)
        v2=get_identified_verbs(pred2)

        if v not in v1 and v in v2:
            correct+=1
            continue
        else:
            print(f"Failed for: [{s1}],[{s2}]. {v} in both did NOT chage the predicate identification")
            print(v1,v2)
            #print(f"{pred1['verbs']=} \n{pred2['verbs']=}")
            print("\n")
    return (len(data)-correct)/len(data)*100


def evaluate_PI_INV_contractions(predictor,data):               
    """
    This function returns a failure rate (percentage) that represents how many coupled sentnece 
    presents inconcitency in their tags of a contracted predicate. The idea is that contracting a verb should not cause any changes! 
    Matching is done as following: tags need to be exactly the same thus the perturbation does not have to introduce
    any more (or less) token or change the arguments. This checks only fits very few purposes.
    :predictor
    :data is a list of lists where the nested lists are couple of sentence to be compared
    """
    fail=0
    for s in data:
        s1,s2=s
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
                if v1['tags']!=v2['tags']:
                    fail+=1
                    print(f"Failure in {s1} | {s2}")
                    print(f"The alteration of verb {v1['verb']}/{v2['verb']} lead to a different labeling:\n")
                    print(v1)
                    print(v2)
                    break
            
    return fail/len(data)*100
