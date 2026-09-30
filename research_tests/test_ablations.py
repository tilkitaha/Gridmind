import unittest
import numpy as np
import torch
from gridmind_research.ablations import AblationPolicy, potential, observation, evaluate
from gridmind_research.battery import BatteryBatch, load_episodes


class AblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.eps=load_episodes('train')[:2]

    def test_potential_telescopes_with_signed_losses(self):
        seq=np.array([[0.,0.,0.],[-1.,0.,1.],[-2.,-2.,-2.],[1.,-1.,0.]])
        ph=potential(seq)
        self.assertAlmostEqual(float(np.diff(ph).sum()),float(ph[-1]-ph[0]))
        self.assertAlmostEqual(float(ph[2]),0.)
        self.assertLess(float(ph[1]),0.)

    def test_fairness_state_is_past_only(self):
        env=BatteryBatch(self.eps);g=np.zeros((2,6));x=observation(env,g,True)
        env.net[:]=99999
        np.testing.assert_array_equal(x,observation(env,g,True))
        np.testing.assert_array_equal(x[...,-2:],0)
        self.assertEqual(x.shape,(2,6,14))

    def test_continuous_support_and_finite_gradient(self):
        for kind in ['IPPO','MAPPO']:
            model=AblationPolicy(kind,'continuous')
            x=torch.as_tensor(BatteryBatch(self.eps).obs());dist=model.distribution(x)
            a=dist.sample();request=model.request(a)
            self.assertTrue(np.all(request>=-.5) and np.all(request<=.5))
            loss=-(dist.log_prob(a)+.01*dist.entropy()).mean()+model.value(x).square().mean()
            loss.backward()
            self.assertTrue(all(torch.isfinite(p.grad).all() for p in model.parameters()))

    def test_both_action_types_preserve_terminal_and_balance(self):
        for action in ['discrete','continuous']:
            z=evaluate(AblationPolicy('MAPPO',action,True),self.eps)
            self.assertLess(z['terminal_residual'],1e-8)
            self.assertLess(z['energy_residual'],1e-8)
            self.assertTrue(np.isfinite(z['cost']).all())


if __name__=='__main__':unittest.main()
