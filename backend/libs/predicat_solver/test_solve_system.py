from unittest import TestCase

from predicat_solver import Predicate, solve_system, solve_system_with_GA


class TestSolveSystem(TestCase):
    def test_solve_system(self):
        system = [
            Predicate(Predicate.POSITIVE_TYPE, [0, 1]),
            Predicate(Predicate.NEGATIVE_TYPE, [0, 1]),
        ]
        solutions = [[False, True], [True, False]]
        self.assertEqual(sorted(solve_system(system)), sorted(solutions))

    def test_solve_system2(self):
        system = [
            Predicate(Predicate.POSITIVE_TYPE, [0]),
            Predicate(Predicate.NEGATIVE_TYPE, [0, 1]),
        ]
        solutions = [[True, False]]
        self.assertEqual(sorted(solve_system(system)), sorted(solutions))

    def test_solve_with_GA(self):
        system = [
            Predicate(Predicate.POSITIVE_TYPE, [0]),
            Predicate(Predicate.NEGATIVE_TYPE, [0, 1]),
        ]
        solution = [1, 0]
        self.assertEqual(solve_system_with_GA(system), solution)