import json,sys
S=sys.argv[1]
med=[json.loads(l) for l in open(S+"/med.jsonl")]
wins=[(100,145),(262,288),(636,672),(712,802),(2005,2042),(2372,2405),(480,536),(550,606),(845,917),(975,1025),(1130,1186),(1240,1322),(1380,1432),(1855,1906),(2940,3026),(3045,3095),(3215,3262),(3440,3520)]
inwin=lambda t:any(a<=t<b for a,b in wins)
W=[]
for d in med: W+=[w for w in d["w"]]
for l in open(S+"/transcript.jsonl"):
    d=json.loads(l); W+=[w for w in d["w"] if not inwin(w[0])]
W.sort()
with open(S+"/words.jsonl","w") as f: f.write(json.dumps({"w":W},ensure_ascii=False)+"\n")
if len(sys.argv)>2:
  for r in sys.argv[2:]:
    a,b=map(float,r.split("-")); print(f"## {r}")
    print(" ".join(f"{w[2].strip()}|{w[0]:.1f}" for w in W if a<=w[0]<b)); print()
