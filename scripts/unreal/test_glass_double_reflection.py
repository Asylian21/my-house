"""Rear-interface energy and mirrored-camera projection contracts (CPU only)."""
import copy
import importlib.util
import json
import math
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

s=importlib.util.spec_from_file_location('glass_double',Path(__file__).with_name('glass-double-reflection.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)


class DoubleGlassTest(unittest.TestCase):
    def test_capture_scheduler_is_fair_bounded_and_waits_for_quiet(self):
        compiler = shutil.which('c++')
        self.assertIsNotNone(compiler, 'A C++ compiler is required to validate the native capture policy')
        source = r'''
#include "BreziDoubleGlassCapturePolicy.h"
#include <array>
#include <cassert>
int main() {
    using namespace BreziDoubleGlass;
    static_assert(MaximumCaptureWidth == 512);
    static_assert(MaximumWarmupCaptures == 2);
    assert(!IsSettled(10.24, 10.0));
    assert(IsSettled(10.25, 10.0));
    assert(!IsSettled(9.0, 10.0)); // World time reset cannot bypass debounce.
    // Continuous motion / door changes never settle, even over many frames.
    for (int i=0;i<600;++i) assert(!IsSettled(i/60.0, i/60.0));
    FrameBudget budget;
    std::array<int, 19> remaining; remaining.fill(2);
    for (unsigned frame=0;frame<38;++frame) {
        int issued=0, winner=-1;
        for (std::size_t actor=0;actor<remaining.size();++actor)
            if (budget.TryAcquire(frame, actor, remaining.size(), [&](auto i){return remaining[i]>0;})) {
                --remaining[actor]; ++issued; winner=actor;
            }
        assert(issued==1);
        assert(winner==int(frame%19)); // Tick order must not starve any pane.
    }
    for (auto count:remaining) assert(count==0);
    assert(!budget.TryAcquire(38, 0, 19, [](auto){return false;}));
    // Invisible panes do not hold the queue; reset-size / destroyed slots safe.
    FrameBudget sparse;
    for (unsigned frame=0;frame<10;++frame) {
        int issued=0, winner=-1;
        for (std::size_t actor=0;actor<19;++actor)
            if (sparse.TryAcquire(frame,actor,19,[](auto i){return i==3||i==17;})) { ++issued; winner=actor; }
        assert(issued==1); assert(winner==(frame%2 ? 17 : 3));
    }
    assert(!sparse.TryAcquire(10,0,0,[](auto){return true;}));
    assert(sparse.TryAcquire(10,0,1,[](auto){return true;}));
}
'''
        with tempfile.TemporaryDirectory(prefix='brezi-glass-policy-') as directory:
            cpp = Path(directory)/'policy.cpp'; executable = Path(directory)/'policy'
            cpp.write_text(source)
            subprocess.run([compiler, '-std=c++17', '-Wall', '-Wextra', '-Werror',
                '-I', str(m.ROOT/'unreal/BreziTwin/Source/BreziTwin'), str(cpp), '-o', str(executable)], check=True, capture_output=True)
            subprocess.run([str(executable)], check=True, capture_output=True)

    def fixture(self):
        base=m.ROOT/'output/unreal/photoreal-20260923-r2'
        if not base.is_dir():self.skipTest('Canonical local fixture absent')
        return json.loads((base/'geometry/scene.json').read_text()),json.loads((base/'model-refresh-import-report.json').read_text())

    def test_semantic_scope_and_reordered_ids(self):
        scene,report=self.fixture();selected=m.select_glass(scene,report)
        self.assertEqual(len(selected),19)
        self.assertTrue(all(b['sourceName']=='real-glass' for b in selected))
        old=selected[0]['id'];new='REORDERED_SOURCE'
        next(x for x in scene['objects'] if x['id']==old)['id']=new
        for b in report['materials']['bindings']:
            if b['id']==old:b['id']=new
        self.assertIn(new,{x['id'] for x in m.select_glass(scene,report)})
        self.assertFalse(any('shower' in b['sourceName'] for b in selected))

    def test_unreviewed_geometry_and_archive_fail(self):
        scene,report=self.fixture();original=copy.deepcopy(scene)
        b=m.select_glass(scene,report)[0];obj=next(x for x in scene['objects'] if x['id']==b['id'])
        obj['boundsMm']['max'][1]+=10
        with self.assertRaisesRegex(RuntimeError,'24 mm'):m.select_glass(scene,report)
        original['activeDesign']['variant']='A'
        with self.assertRaisesRegex(RuntimeError,'active C/B/B'):m.select_glass(original,report)

    def test_first_return_energy_is_bounded_without_darkening_primary(self):
        no_absorption=m.energy(1,[1,1,1]);f=((1.52-1)/(1.52+1))**2
        self.assertAlmostEqual(no_absorption['front'],.042579994960947345)
        self.assertAlmostEqual(no_absorption['rear'][0],f*(1-f)**2)
        self.assertAlmostEqual(no_absorption['transmission'][0],(1-f)**2)
        self.assertAlmostEqual(no_absorption['front']+no_absorption['rear'][0]+no_absorption['transmission'][0],1-f*f*(1-f))
        for cosine in [0,.001,.05,.25,.5,.8,1]:
            e=m.energy(cosine)
            for rear,transmission in zip(e['rear'],e['transmission']):
                self.assertGreaterEqual(rear,0)
                self.assertLessEqual(e['front']+rear+transmission,1+1e-12)
        self.assertLess(m.energy(1)['rear'][0],m.energy(1)['rear'][1])

    def test_mirror_involution_both_camera_sides(self):
        for eye in [[100,5,50],[-100,5,50]]:
            plane=[-2.4,0,0];normal=[1,0,0]
            reflected=m.mirror(eye,plane,normal)
            self.assertAlmostEqual(m.dot(m.sub(eye,plane),normal),-m.dot(m.sub(reflected,plane),normal))
            for a,b in zip(m.mirror(reflected,plane,normal),eye):self.assertAlmostEqual(a,b)

    def test_projected_reflection_matches_real_rear_ray(self):
        eye=[100,0,50];front_hit=[0,5,55];rear=[-2.4,0,0];n=[1,0,0]
        capture=m.mirror(eye,rear,n);f=[1,0,0];r=[0,1,0];u=[0,0,1]
        uv=m.project_rear(front_hit,eye,rear,n,capture,f,r,u,math.tan(math.radians(60/2)),16/9)
        # Physical rear-plane mirror ray hits the rear plane at(-2.4,5.12,55.12)
        # and the same captured ray then reaches this real scene location.
        scene_point=[100,10.24,60.24];w=m.sub(scene_point,capture);z=m.dot(w,f)
        expected=[.5+.5*m.dot(w,r)/(z*math.tan(math.radians(30))),.5-.5*m.dot(w,u)*(16/9)/(z*math.tan(math.radians(30)))]
        for a,b in zip(uv,expected):self.assertAlmostEqual(a,b)

    def test_second_image_shift_is_depth_dependent(self):
        eye=[100,0,50]
        def hit(scene_point,plane):
            virtual=m.mirror(scene_point,plane,[1,0,0]);direction=m.sub(virtual,eye)
            return eye[1]+direction[1]*(-eye[0]/direction[0])
        shifts=[]
        for depth in [20,100]:
            p=[depth,10,50]
            shifts.append(hit(p,[-2.4,0,0])-hit(p,[0,0,0]))
        self.assertTrue(all(x<0 for x in shifts))
        self.assertGreater(abs(shifts[0]),abs(shifts[1])*2)


if __name__=='__main__':unittest.main()
