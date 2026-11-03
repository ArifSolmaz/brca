"""A self-contained, fictional learning lesson. Never imports the clinical model."""
import json
import math
from functools import lru_cache
from pathlib import Path
import streamlit as st

# Abstract measurements with no clinical meaning; deliberately not perfectly separable.
EXAMPLES = [(-1.5,-1,0),(-1,-.2,0),(-.5,1,1),(0,-1,0),(.2,.4,0),(.6,-.5,1),(1,.7,1),(1.5,1,1)]


def objective(weights, penalty, examples=EXAMPLES):
    total = 0
    for a, b, y in examples:
        z = weights[0]+weights[1]*a+weights[2]*b
        total += max(z, 0)-y*z+math.log1p(math.exp(-abs(z)))
    return total/len(examples)+penalty/2*(weights[1]**2+weights[2]**2)


def snapshot(weights, penalty, examples=EXAMPLES):
    rows = []
    for a, b, y in examples:
        z = weights[0]+weights[1]*a+weights[2]*b
        p = 1/(1+math.exp(-z)) if z >= 0 else math.exp(z)/(1+math.exp(z))
        rows.append(dict(a=a,b=b,y=y,p=p,error=p-y))
    gradients = [sum(r['error']*([1,r['a'],r['b']][j]) for r in rows)/len(rows)
                 + (penalty*weights[j] if j else 0) for j in range(3)]
    return dict(weights=list(weights),rows=rows,gradient=gradients,loss=objective(weights,penalty,examples))


@lru_cache(maxsize=9)
def trajectory(rate=.5, penalty=.1, examples=tuple(EXAMPLES)):
    state = snapshot([0,0,0],penalty,examples)
    history = [state]
    for _ in range(60):
        state = snapshot([w-rate*g for w,g in zip(state['weights'],state['gradient'])],penalty,examples)
        history.append(state)
    return history


def lesson_html(lang):
    payload = {'lang':lang,'examples':EXAMPLES}
    assets = Path(__file__).parent/'assets/model_details'
    template = (assets/'learning_demo.html').read_text()
    return template.replace('__LESSON_DATA__',json.dumps(payload,separators=(',',':'))).replace(
        '__LESSON_MATH__',(assets/'learning_math.js').read_text())


def render_learning_demo(lang):
    st.iframe(lesson_html(lang), height="content")
