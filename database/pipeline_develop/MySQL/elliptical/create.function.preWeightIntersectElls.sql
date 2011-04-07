DROP FUNCTION IF EXISTS preWeightIntersectElls;

DELIMITER //

/**
 * This boolean functions determines if two ellipses intersect.
 * The arguments for for ellipse 1 (e1_*) are the centre (ra,decl)
 * and the semi-major and semi-minor axes (ra_err,decl_err). All
 * units are in degrees.
 * The input should be typical the source position in ra and dec,
 * and the errors on the position (in degrees). 
 * It is assumed that a preselection is done so that the two ellipses
 * are close together, and that the ellipses are either alligned or
 * perpendicular oriented wrt each other. 
 * No ra-inflation has to be taken into account.
 */
CREATE FUNCTION preWeightIntersectElls(ie1_ra DOUBLE
                               ,ie1_decl DOUBLE
                               ,ie1_ra_err DOUBLE
                               ,ie1_decl_err DOUBLE
                               ,ie2_ra DOUBLE
                               ,ie2_decl DOUBLE
                               ,ie2_ra_err DOUBLE
                               ,ie2_decl_err DOUBLE
                               ) RETURNS DOUBLE 
DETERMINISTIC

BEGIN
  DECLARE ready BOOLEAN DEFAULT FALSE;
  DECLARE intersect BOOLEAN DEFAULT FALSE;
  DECLARE weight DOUBLE DEFAULT -1;

  DECLARE e1_a DOUBLE DEFAULT NULL;
  DECLARE e1_b DOUBLE DEFAULT NULL;
  DECLARE e1_pa DOUBLE DEFAULT NULL;
  DECLARE e2_a DOUBLE DEFAULT NULL;
  DECLARE e2_b DOUBLE DEFAULT NULL;
  DECLARE e2_pa DOUBLE DEFAULT NULL;

  DECLARE theta_rot DOUBLE DEFAULT NULL;
  DECLARE e2_phi DOUBLE DEFAULT NULL;

  DECLARE e1_q1 DOUBLE DEFAULT NULL;
  DECLARE e1_q3 DOUBLE DEFAULT NULL;
  DECLARE e1_q6 DOUBLE DEFAULT NULL;

  DECLARE distance DOUBLE DEFAULT NULL;
  DECLARE e2_h DOUBLE DEFAULT NULL;
  DECLARE e2_k DOUBLE DEFAULT NULL;
  DECLARE e2_h_acc DOUBLE DEFAULT NULL;
  DECLARE e2_k_acc DOUBLE DEFAULT NULL;
  DECLARE e2_q1 DOUBLE DEFAULT NULL;
  DECLARE e2_q2 DOUBLE DEFAULT NULL;
  DECLARE e2_q3 DOUBLE DEFAULT NULL;
  DECLARE e2_q4 DOUBLE DEFAULT NULL;
  DECLARE e2_q5 DOUBLE DEFAULT NULL;
  DECLARE e2_q6 DOUBLE DEFAULT NULL;

  DECLARE v0 DOUBLE DEFAULT NULL;
  DECLARE v1 DOUBLE DEFAULT NULL;
  DECLARE v2 DOUBLE DEFAULT NULL;
  DECLARE v3 DOUBLE DEFAULT NULL;
  DECLARE v4 DOUBLE DEFAULT NULL;
  DECLARE v5 DOUBLE DEFAULT NULL;
  DECLARE v6 DOUBLE DEFAULT NULL;
  DECLARE v7 DOUBLE DEFAULT NULL;
  DECLARE v8 DOUBLE DEFAULT NULL;

  DECLARE alpha0 DOUBLE DEFAULT NULL;
  DECLARE alpha1 DOUBLE DEFAULT NULL;
  DECLARE alpha2 DOUBLE DEFAULT NULL;
  DECLARE alpha3 DOUBLE DEFAULT NULL;
  DECLARE alpha4 DOUBLE DEFAULT NULL;

  DECLARE delta0 DOUBLE DEFAULT NULL;
  DECLARE delta1 DOUBLE DEFAULT NULL;
  DECLARE delta2 DOUBLE DEFAULT NULL;
  DECLARE eta0 DOUBLE DEFAULT NULL;
  DECLARE eta1 DOUBLE DEFAULT NULL;
  DECLARE vartheta0 DOUBLE DEFAULT NULL;
  
  DECLARE s_f0 INT DEFAULT NULL;
  DECLARE s_f1 INT DEFAULT NULL;
  DECLARE s_f2 INT DEFAULT NULL;
  DECLARE s_f3 INT DEFAULT NULL;
  DECLARE s_f4 INT DEFAULT NULL;

  DECLARE sign_change_neg INT DEFAULT NULL;
  DECLARE sign_change_pos INT DEFAULT NULL;
  DECLARE Nroots INT DEFAULT NULL;

  DECLARE y1 DOUBLE;
  DECLARE y1_root DOUBLE;
  DECLARE y2 DOUBLE;
  DECLARE y3 DOUBLE;
  DECLARE y4 DOUBLE;

  DECLARE e1_x1 DOUBLE;
  DECLARE e1_x2 DOUBLE;
  DECLARE e2_x1 DOUBLE;
  DECLARE e2_x2 DOUBLE;

  DECLARE abc_a DOUBLE;
  DECLARE abc_b DOUBLE;
  DECLARE abc_c DOUBLE;
  DECLARE abc_D DOUBLE;

  /**
   * We convert from degrees to arcseconds
   */
  SET e1_a = 3600 * GREATEST(ie1_ra_err, ie1_decl_err);
  SET e1_b = 3600 * LEAST(ie1_ra_err, ie1_decl_err);
  IF ie1_ra_err > ie1_decl_err THEN
    /*TODO: adjust*/
    SET e1_pa = 70;
  ELSE 
    SET e1_pa = 0;
  END IF;
  SET e2_a = 3600 * GREATEST(ie2_ra_err, ie2_decl_err);
  SET e2_b = 3600 * LEAST(ie2_ra_err, ie2_decl_err);
  IF ie2_ra_err > ie2_decl_err THEN
    SET e2_pa = 120;
  ELSE 
    SET e2_pa = 0;
  END IF;

  SET e2_h = 3600 * (ie1_ra - ie2_ra);
  SET e2_k = 3600 * (ie2_decl - ie1_decl);

  SET theta_rot = RADIANS(e1_pa - 90);
  SET e2_phi = RADIANS(e2_pa - e1_pa);

  SET e2_h_acc =  e2_h * COS(theta_rot) + e2_k * SIN(theta_rot);
  SET e2_k_acc = -e2_h * SIN(theta_rot) + e2_k * COS(theta_rot);

  /* We drop the _acc suffix */
  SET e2_h = e2_h_acc;
  SET e2_k = e2_k_acc;

  /** 
   * These tests can be executed immediately, to know
   * whether one there is separation or containment.
   */
  SET distance = SQRT(e2_h * e2_h + e2_k * e2_k);
  IF distance > (e1_a + e2_a) THEN
    SET intersect = FALSE;
    SET ready = TRUE;
  END IF;

  IF ready = FALSE THEN
    IF distance <= (e1_b + e2_b) THEN
      SET intersect = TRUE;
      SET ready = TRUE;
    END IF;
  END IF;

  /**
   * If the ellipses are to far there is separation and 
   * the ellipses do not intersect.
   * If the ellipses are to close there is intersection 
   * and we are done as well.
   * The other cases we have to evaluate.
   */
  IF (ready = FALSE) THEN

    SET e1_q1 = e1_a * e1_a;
    SET e1_q6 = e1_b * e1_b;
    SET e1_q3 = -e1_q1 * e1_q6;

    SET e2_q1 = e2_a * e2_a * COS(e2_phi) * COS(e2_phi) 
                + e2_b * e2_b * SIN(e2_phi) * SIN(e2_phi);
    SET e2_q6 = e2_a * e2_a * SIN(e2_phi) * SIN(e2_phi)
                + e2_b * e2_b * COS(e2_phi) * COS(e2_phi);
    SET e2_q4 = (e2_b * e2_b - e2_a * e2_a) * SIN(2 * e2_phi);
    SET e2_q2 = -2 * e2_k * e2_q1 - e2_h * e2_q4;
    SET e2_q3 = e2_h * e2_h * e2_q6 + e2_k * e2_k * e2_q1 
                + e2_h * e2_k * e2_q4 - e2_a * e2_a * e2_b * e2_b;
    SET e2_q5 = -2 * e2_h * e2_q6 - e2_k * e2_q4;

    SET v0 = e1_q6 * e2_q4;
    SET v1 = e1_q6 * e2_q1 - e2_q6 * e1_q1;
    SET v2 = e1_q6 * e2_q5;
    SET v3 = e1_q6 * e2_q2;
    SET v4 = e1_q6 * e2_q3 - e2_q6 * e1_q3;
    SET v5 = -e2_q4 * e1_q1;
    SET v6 = -e2_q4 * e1_q3;
    SET v7 = e1_q1 * e2_q5;
    SET v8 = -e2_q5 * e1_q3;

    /**
     * The coefficients of the Bezout determinant
     */
    SET alpha0 = v2 * v8 - v4 * v4;
    SET alpha1 = v0 * v8 + v2 * v6 - 2 * v3 * v4;
    SET alpha2 = v0 * v6 - v2 * v7 - v3 * v3 - 2 * v1 * v4;
    SET alpha3 = -v0 * v7 + v2 * v5 - 2 * v1 * v3;
    SET alpha4 = v0 * v5 - v1 * v1;

    SET alpha0 = alpha0 / alpha4;
    SET alpha1 = alpha1 / alpha4;
    SET alpha2 = alpha2 / alpha4;
    SET alpha3 = alpha3 / alpha4;
    SET alpha4 = 1;

    SET delta2 = ((3 * alpha3 * alpha3) / (16 * alpha4)) - (alpha2/2);
    SET delta1 = ((alpha2 * alpha3) / (8 * alpha4)) - ((3 * alpha1)/4);
    SET delta0 = (alpha1 * alpha3 / (16 * alpha4)) - alpha0;
    SET eta1 = (delta1/delta2) * 
               (3 * alpha3 - (4 * (alpha4 * delta1 / delta2))) - 
               (2 * alpha2 - (4 * (alpha4 * delta0 / delta2))); 
    SET eta0 = (delta0/delta2) * 
               (3 * alpha3 - (4 * (alpha4 * delta1 / delta2))) - 
               (alpha1);
    SET vartheta0 = (eta0/eta1) * 
                    (delta1 - (eta0 * delta2 / eta1)) - delta0;

    /**
     * Determine sign for -infty
     */
    SET s_f0 = SIGN(alpha4);
    SET s_f1 = SIGN((-4*alpha4));
    SET s_f2 = SIGN(delta2);
    SET s_f3 = SIGN(-eta1);
    SET s_f4 = SIGN(vartheta0);

    SET sign_change_neg = 0;
  
    IF s_f0 * s_f1 < 0 THEN
      SET sign_change_neg = sign_change_neg + 1;
    END IF;
    IF s_f1 * s_f2 < 0 THEN
      SET sign_change_neg = sign_change_neg + 1;
    END IF;
    IF s_f2 * s_f3 < 0 THEN
      SET sign_change_neg = sign_change_neg + 1;
    END IF;
    IF s_f3 * s_f4 < 0 THEN
      SET sign_change_neg = sign_change_neg + 1;
    END IF;

    /**
     * Determine sign for +infty
     */
    SET s_f0 = SIGN(alpha4);
    SET s_f1 = SIGN((4*alpha4));
    SET s_f2 = SIGN(delta2);
    SET s_f3 = SIGN(eta1);
    SET s_f4 = SIGN(vartheta0);

    SET sign_change_pos = 0;
  
    IF s_f0 * s_f1 < 0 THEN
      SET sign_change_pos = sign_change_pos + 1;
    END IF;
    IF s_f1 * s_f2 < 0 THEN
      SET sign_change_pos = sign_change_pos + 1;
    END IF;
    IF s_f2 * s_f3 < 0 THEN
      SET sign_change_pos = sign_change_pos + 1;
    END IF;
    IF s_f3 * s_f4 < 0 THEN
      SET sign_change_pos = sign_change_pos + 1;
    END IF;

    SET Nroots = sign_change_neg - sign_change_pos;
    IF Nroots > 0 THEN
      SET intersect = TRUE;
    ELSE
      SET intersect = FALSE;
    END IF;
  
  END IF; 
  
  /* RETURN intersect;
   * And here we go further,
   * we will compute the points of intersection of the two ellipses.
   * TODO: check overlap
   * Then we calculate the area integrating from theta_0 to theta_1
   */

  IF intersect = TRUE THEN
    CALL getQuarticRoots(alpha4
                        ,alpha3
                        ,alpha2
                        ,alpha1
                        ,alpha0
                        ,y1
                        ,y2
                        ,y3
                        ,y4
                        );
    IF y1 IS NULL THEN
      /* check solutions in ellipse 1:
       * E1: e1_q1 y^2 + e1_q3 + e1_q6 x^2
       */
      SET y1_root = (-e1_q1 * y1 * y1 - e1_q3) / e1_q6;
      IF y1_root >= 0 THEN
        SET e1_x1 = SQRT(y1_root);
        SET e1_x2 = -x1;
        /* Now we check the solutions in ellipse 2:
         * E2(x,y) = (e2_q1 y^2 + e2_q2 y + e2_q3) 
         *           + (e2_q4 y + e2_q5) x 
         *           + e2_q6 x^2 = 0
         * We have sol. y1, check quadr eq. discr.
         */
        SET abc_a = e2_q6;
        SET abc_b = e2_q4 * y1 + e2_q5;
        SET abc_c = e2_q1 * y1 * y1 + e2_q2 * y1 + e2_q3;
        SET abc_D = abc_b * abc_b - 4 * abc_a * abc_c;
        IF abc_D >= 0 THEN
          SET e2_x1 = (-abc_b + SQRT(abc_D)) / (2 * abc_a);
          SET e2_x2 = (-abc_b - SQRT(abc_D)) / (2 * abc_a);
        /*
        ELSE
          No real sol.
        */
        END IF;
        /* and now compare the sol.
      /*
      ELSE
        No real solutions 
      */
      END IF;
    END IF;
  ELSE
    SET weight = -1;
  END IF;

  RETURN alpha0;

END;
//

DELIMITER ;
