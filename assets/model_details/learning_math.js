/* Fictional classroom arithmetic only. No clinical model or patient records. */
const ToyLearning = (() => {
 function valid(rows) {
  return Array.isArray(rows) && rows.length === 8 && rows.every(r =>
   Array.isArray(r) && r.length === 3 && r.every(Number.isFinite) &&
   Math.abs(r[0]) <= 3 && Math.abs(r[1]) <= 3 && (r[2] === 0 || r[2] === 1));
 }
 function snapshot(weights, penalty, examples) {
  if (!valid(examples)) throw Error('Invalid fictional examples');
  const rows = examples.map(([a,b,y]) => {
   const z = weights[0] + weights[1]*a + weights[2]*b;
   const p = z >= 0 ? 1/(1+Math.exp(-z)) : Math.exp(z)/(1+Math.exp(z));
   const loss = Math.max(z,0) - y*z + Math.log1p(Math.exp(-Math.abs(z)));
   return {a,b,y,p,error:p-y,loss};
  });
  const gradient = weights.map((w,j) => rows.reduce((sum,r) => sum+r.error*[1,r.a,r.b][j],0)/rows.length + (j ? penalty*w : 0));
  const loss = rows.reduce((sum,r)=>sum+r.loss,0)/rows.length + penalty/2*(weights[1]**2+weights[2]**2);
  return {weights:[...weights],rows,gradient,loss};
 }
 function trajectory(rate, penalty, examples) {
  if (![.1,.5,1].includes(rate) || ![0,.1,.5].includes(penalty)) throw Error('Invalid lesson settings');
  const history=[snapshot([0,0,0],penalty,examples)];
  for(let i=0;i<60;i++) {
   const old=history[history.length-1];
   history.push(snapshot(old.weights.map((w,j)=>w-rate*old.gradient[j]),penalty,examples));
  }
  return history;
 }
 return {valid,snapshot,trajectory};
})();
if (typeof module !== 'undefined' && module.exports) module.exports = ToyLearning;
