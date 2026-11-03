"""Verify the fictional lesson math independently of clinical prediction code."""
import ast
import math
import json
import subprocess
import unittest
from pathlib import Path
from learning_demo import EXAMPLES, objective, snapshot, trajectory, lesson_html

class LearningLessonTests(unittest.TestCase):
    def test_browser_rejects_blank_nonbinary_and_out_of_plot_inputs(self):
        root=Path(__file__).resolve().parents[1]
        blank=[list(r) for r in EXAMPLES];blank[0][0]=''
        label=[list(r) for r in EXAMPLES];label[0][2]=2
        far=[list(r) for r in EXAMPLES];far[0][1]=3.01
        script="""const fs=require('fs'),m=require(process.argv[1]);
        const rows=JSON.parse(fs.readFileSync(0,'utf8'));
        process.stdout.write(JSON.stringify(rows.map(m.valid)));"""
        result=subprocess.run(['node','-e',script,str(root/'assets/model_details/learning_math.js')],
            input=json.dumps([EXAMPLES,blank,label,far]),text=True,capture_output=True,check=True)
        self.assertEqual(json.loads(result.stdout),[True,False,False,False])

    def test_browser_solver_matches_python_after_feature_and_label_edits(self):
        root=Path(__file__).resolve().parents[1]
        flipped=[list(r) for r in EXAMPLES];flipped[0][2]=1
        moved=[list(r) for r in EXAMPLES];moved[2][:2]=[2.8,-2.6]
        all_one=[[a,b,1] for a,b,_ in EXAMPLES]
        cases=[{'rows':rows,'rate':rate,'penalty':penalty}
               for rows in [EXAMPLES,flipped,moved,all_one]
               for rate,penalty in [(.5,.1),(1,0),(1,.5)]]
        script="""const fs=require('fs'),m=require(process.argv[1]);
        const cases=JSON.parse(fs.readFileSync(0,'utf8'));
        process.stdout.write(JSON.stringify(cases.map(c=>m.trajectory(c.rate,c.penalty,c.rows))));"""
        result=subprocess.run(['node','-e',script,str(root/'assets/model_details/learning_math.js')],
                              input=json.dumps(cases),text=True,capture_output=True,check=True)
        histories=json.loads(result.stdout)
        for case,history in zip(cases,histories):
            expected=trajectory(case['rate'],case['penalty'],tuple(tuple(r) for r in case['rows']))
            for actual,reference in zip(history,expected):
                self.assertAlmostEqual(actual['loss'],reference['loss'],places=10)
                for key in ['weights','gradient']:
                    for a,b in zip(actual[key],reference[key]):self.assertAlmostEqual(a,b,places=10)
                for a,b in zip(actual['rows'],reference['rows']):self.assertAlmostEqual(a['p'],b['p'],places=10)
        self.assertNotEqual(histories[0][1]['weights'],histories[3][1]['weights'])
        self.assertNotEqual(histories[0][20]['weights'],histories[6][20]['weights'])

    def test_gradient_matches_independent_finite_differences(self):
        for penalty in [0,.1,.5]:
            weights=[.2,-.4,.7]
            analytic=snapshot(weights,penalty)['gradient']
            for j in range(3):
                plus=list(weights);minus=list(weights)
                plus[j]+=1e-6;minus[j]-=1e-6
                numeric=(objective(plus,penalty)-objective(minus,penalty))/2e-6
                self.assertAlmostEqual(analytic[j],numeric,places=8)

    def test_all_playback_paths_recompute_predictions_and_updates(self):
        for rate in [.1,.5,1]:
            for penalty in [0,.1,.5]:
                history=trajectory(rate,penalty)
                self.assertEqual(len(history),61)
                self.assertEqual(history[0]['weights'],[0,0,0])
                self.assertAlmostEqual(history[0]['loss'],math.log(2))
                self.assertTrue(all(r['p']==.5 for r in history[0]['rows']))
                for old,new in zip(history,history[1:]):
                    for j in range(3):
                        self.assertAlmostEqual(new['weights'][j],old['weights'][j]-rate*old['gradient'][j])
                    self.assertLessEqual(new['loss'],old['loss']+1e-12)
                    for row,(a,b,y) in zip(new['rows'],EXAMPLES):
                        self.assertEqual(row['y'],y)
                        self.assertAlmostEqual(row['p'],1/(1+math.exp(-(new['weights'][0]+new['weights'][1]*a+new['weights'][2]*b))))

    def test_lesson_has_both_languages_and_no_clinical_model_dependency(self):
        tree=ast.parse((Path(__file__).resolve().parents[1]/'learning_demo.py').read_text())
        imports=[node.module for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
        imports += [alias.name for node in ast.walk(tree) if isinstance(node,ast.Import) for alias in node.names]
        self.assertNotIn('brca_core',imports)
        for lang in ['tr','en']:
            html=lesson_html(lang)
            self.assertNotIn('__LESSON_DATA__',html)
            self.assertIn('kurgu',html)
            self.assertIn('fictional',html)
            self.assertIn('id="ld-back"',html)
            self.assertIn('id="ld-next"',html)
            self.assertIn('id="ld-play"',html)
            self.assertIn('<math display="block">',html)
