""" Find parameters for trapez shaped key caps for the index fingers

Problem: with a simple big key cap as third cap for the index finger, it is difficult hit exactly all combos.

Idea: Add a bend to the big key cap.
      More exactly: - Make a sticked combination from a "normal" cap pair
                    - rotate it to outward symmetric (the big one and the two small ones)
                    - enlarge the caps so, that the hole in the middle will be filled
                      => the caps must get a trapez shape
       ____ ____
      /___/ \___\   
      \___\ /___/
        |     |
        |   two seperated small caps
      a combined big cap
        
"""

import math

DEGREE = float


def main():
    param_finder = TrapezIndexFingerCapsParametersFinder()
    param_finder.calc(outward_rotating_angle=15)


class TrapezIndexFingerCapsParametersFinder:
    SMALL_CAP_TILT_ANGLE = 15  # 15 degree for each side, s. case/fingerparts.py/SwitchPairHolderCreator.TILT_ANGLE
    BIG_CAP_TILT_ANGLE = 25  # the tilt for the base of the switch, s. case/fingerparts.py/SingleSwitchHolderCreator.TILT_ANGLE

    def __init__(self):
        """
        For simplifying reason, the recangle for every switch, should be a square with length 1

               y
           ____|B___           B: x=0, y>0, z=0
        __/___/ \A__\__ x      A: x>0, y=0, z>0
          \___\ /___/
               |

        """
        pass

    def calc(self, outward_rotating_angle: DEGREE):
        """
            pairs_tilt_angle: rotating angle of big cap and the small caps about the y axis
        """
        a_z = self._calc_z_of_point_a()  # before outward rotating
        b_y = self._calc_y_of_point_b()
        a_x = self._calc_x_of_point_a(outward_rotating_angle=outward_rotating_angle, a_z=a_z)
        enlarging_factor = self._calc_enlarging_factor(outward_rotating_angle=outward_rotating_angle, a_z=a_z)
        print(f'enlarging_factor: {enlarging_factor}')

    def _calc_z_of_point_a(self) -> float:
        """
                z
                |
         _______|____B____ y
            \   |   /
              \ |*/     *: alpha angle
                A       angle between y axis and A-B: SMALL_CAP_TILT_ANGLE
        """
        radians = math.pi / 180
        alpha = (90 - self.SMALL_CAP_TILT_ANGLE) * radians
        z = math.cos(alpha)
        return z
    
    def _calc_y_of_point_b(self) -> float:
        """
                z
                |
         _______|____B____ y
            \   |   /
              \ |*/     *: alpha angle
                A       angle between y axis and A-B: SMALL_CAP_TILT_ANGLE
        """
        radians = math.pi / 180
        alpha = (90 - self.SMALL_CAP_TILT_ANGLE) * radians
        y = math.sin(alpha)
        return y
    
    def _calc_x_of_point_a(self, outward_rotating_angle: DEGREE, a_z: float) -> float:
        """ rotate the caps holder pair around the y axis: A -> A'

                z
                |
         _______|________ x
                |    
                |    A'
                A        

        a_z:    the z value of A
        return: the x value of A'
        """
        angle_in_radians = outward_rotating_angle * math.pi / 180
        x = a_z * math.sin(angle_in_radians)
        return x


    def _calc_enlarging_factor(self, outward_rotating_angle: DEGREE, a_z: float) -> float:
        """ how much must the base line be, to fill the gap
        
        rotate the caps holder pair around the y axis: A -> A'

                z
                |                 |\
         _______|________ x       |*\      *: outward_rotating_angle
                |                 |  \ A'  90°
                |    A'           A  /
                A                 | b
                                  |/

        a_z:    the z value of A
        return: the x value of A'

        =>
              __a___
             /     |  the shape of the upper smaller cap
            /___b__|

            a: the "normal" width of the cap (simplified to 1)
            b: the new width at the bend (this is the enlarging factor)
        """
        angle_in_radians = outward_rotating_angle * math.pi / 180
        b = 1 + math.tan(angle_in_radians)
        return b


if __name__ == '__main__':
    main()
