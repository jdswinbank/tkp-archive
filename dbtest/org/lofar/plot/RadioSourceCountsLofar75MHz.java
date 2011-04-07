package org.lofar.plot;

import java.awt.Color;
import java.sql.*;
import java.text.NumberFormat;
import java.text.SimpleDateFormat;

import javax.swing.JPanel;

import org.jfree.chart.*;
import org.jfree.chart.axis.*;
import org.jfree.chart.plot.*;
import org.jfree.chart.renderer.xy.*;
import org.jfree.data.time.*;
import org.jfree.data.xy.*;
import org.jfree.ui.*;

public class RadioSourceCountsLofar75MHz extends ApplicationFrame {

    public RadioSourceCountsLofar75MHz(String title) {
        super(title);
	//double[][] coord = getWenssCoordinates();
        XYDataset dataset = createDataset();
        JFreeChart chart = createChart(dataset);
        ChartPanel chartPanel = new ChartPanel(chart, false);
        chartPanel.setPreferredSize(new java.awt.Dimension(1024, 712));
        chartPanel.setMouseZoomable(true, false);
        setContentPane(chartPanel);
    }

    private static JFreeChart createChart(XYDataset dataset) {

        //JFreeChart chart = ChartFactory.createScatterPlot(
        JFreeChart chart = ChartFactory.createXYLineChart(
            "Expected source counts at 75 MHz for LOFAR",  // title
            "S",
            "dN/dS (sr^-1)",
            dataset,            // data
	    PlotOrientation.VERTICAL,
            true,               // create legend?
            false,               // generate tooltips?
            false               // generate URLs?
        );

        chart.setBackgroundPaint(Color.white);

        XYPlot plot = (XYPlot) chart.getPlot();
        plot.setBackgroundPaint(Color.lightGray);
        plot.setDomainGridlinePaint(Color.white);
        plot.setRangeGridlinePaint(Color.white);
        plot.setAxisOffset(new RectangleInsets(5.0, 5.0, 5.0, 5.0));
        //plot.setDomainCrosshairVisible(true);
        //plot.setRangeCrosshairVisible(true);
        
        XYLineAndShapeRenderer renderer = new XYLineAndShapeRenderer();
        //renderer.setDefaultShapesVisible(true);
        //renderer.setDefaultShapesFilled(true);
	plot.setRenderer(renderer);

        //NumberAxis domainAxis = (NumberAxis) plot.getDomainAxis();
        //NumberAxis rangeAxis = (NumberAxis) plot.getRangeAxis();
	NumberAxis domainAxis = new LogarithmicAxis("S");
	NumberAxis rangeAxis = new LogarithmicAxis("dN/dS (sr^-1)");// array om links en rechts waarden te displayen!
	plot.setDomainAxis(domainAxis);
	plot.setRangeAxis(rangeAxis);
	//rangeAxis.setRange(0.001, 1000);
	//domainAxis.setRange(0.01, 100);
        return chart;
    }
    
    private static XYDataset createDataset() {

        double S = 0, Smin = 0.001, Smax = 10, Sfirst = 0;
        double dS = 0;
	double N = 0;
	final double[] a = {0.841, 0.540, 0.364, -0.063, -0.107, 0.052, -0.007};
	double fac = 0, sum = 0;
	int block = 0;
	double noem = 0;

	final double[] nu = {30, 75, 120, 200, 330, 1400};
	XYSeries[] s = new XYSeries[nu.length];
	for (int k = 0; k < nu.length; k++) {
		//System.out.println("Plotting for nu[" + k + "] = " + nu[k]);
		s[k] = new XYSeries("Extragalactic Source Counts at Lofar's " + nu[k] + "MHz");
		//System.out.println("dSnu \t Snu \t fac1 \t sum \t Snu \t N");
		//System.out.println("---------------------------");
		double scale = Math.pow((nu[k]/1400), 0.7);
		//System.out.println("Scale: " + scale);
		double Snu = 0, dSnu = 0;
		double Snu_min = 0.001, Snu_first = 0;
		double fac1 = 0, fac2 = 0;
		N = 0; sum = 0; block = 0;
		while (Snu <= Smax) {
			Snu_first = Snu_min * Math.pow(10, block);
			dSnu = Snu_first;
			Snu = Snu_first;
			for (int l = 0; l < 9 & Snu <= Smax; l++) {
				//System.out.println("Math.pow((scale * Snu), 2.5): " + Math.pow((scale * Snu), 2.5));
				fac1 = 1. / Math.pow((scale * Snu), 2.5);
				sum = 0;
				for (int i = 0; i < a.length; i++) {
					fac2 = a[i] * (Math.pow(Math.log10(scale * Snu * 1000), i));
					sum = sum + fac2;
				}
				N = fac1 * Math.pow(10, sum) * scale; 
				//System.out.println(dSnu + "\t" + Snu + "\t" + fac1 + "\t" + "\t" + sum + "\t" + N);
				s[k].add(Snu, N);
				Snu = Snu + dSnu;
			}
			block++;
			//System.out.println("Last values: " + dSnu + "\t" + fac1 + "\t" + sum + "\t" + Snu + "\t" + N);
		}
	}


	// En hier integreren we nu = 75
	// aannemende dat er geen rand is...
	/*System.out.println("dS \t mdS \t dN \t N"); 
	dS = dS / 100;
	double mdS = Smin; 
	N = 0;
	double dN = 0;
	while (mdS < Smax) {
		dN = 3 * mdS * mdS * dS;
		N += dN;
		System.out.println(dS + "\t" + mdS + "\t" + dN + "\t" + N); 
		mdS = mdS + dS;
	}
	System.out.println("Laatste waarden: " + dS + "\t" + mdS + "\t" + dN + "\t" + N); */
	
	/*dS = dS / 100;
        double mdS = Smin;
        N = 0;
        double dN = 0;
        while (mdS < Smax) {
                dN = 3 * mdS * mdS * dS;
                N += dN;
                System.out.println(dS + "\t" + mdS + "\t" + dN + "\t" + N);
                mdS = mdS + dS;
        }*/

	double[] FoV = {650, 250, 160, 95, 156, 3437.75};
	// in mJy/beam
	double[] Snu_low = {0.35, 0.24, 0.013, 0.011, 0.00090, 0.15};
	for (int k = 4; k < 5; k++) {
                System.out.println("Integrating for nu[" + k + "] = " + nu[k] + " MHz:");
                System.out.println("dSnu \t mdSnu \t dN \t N");
                System.out.println("------- start integration --------------------");
                double scale = Math.pow((nu[k]/1400), 0.7);
                double Snu = 0, dSnu = 0, mdSnu = 0, dN = 0;
		// Snu_min can be chosen conveniently, 
		// depending on the 3sigma senisitivity at the specific frequency,
		// which is 240 mJy/bm for Lofar's 75 MHz.
                double Snu_min = 0.0001, Snu_first = 0;
                double fac1 = 0, fac2 = 0;
                N = 0; dN = 0; sum = 0; block = 0;
		//Smax = 1.1;
                while (mdSnu <= Smax) {
                        Snu_first = Snu_min * Math.pow(10, block);
                        dSnu = Snu_first / 10;
                        mdSnu = Snu_first;
                        for (int l = 0; l < 90 & mdSnu <= Smax; l++) {
                                fac1 = 1. / Math.pow((scale * mdSnu), 2.5);
                                sum = 0;
                                for (int i = 0; i < a.length; i++) {
                                        fac2 = a[i] * (Math.pow(Math.log10(scale * mdSnu * 1000), i));
                                        sum = sum + fac2;
                                }
                                dN = fac1 * Math.pow(10, sum) * scale * dSnu;
				if (mdSnu > Snu_low[k]) {
					N += dN;
        	                        System.out.println(dSnu + "\t" + mdSnu + "\t" + dN + "\t" + N);
				}
                                mdSnu = mdSnu + dSnu;
                        }
                        block++;
                        //System.out.println(dSnu + "\t" + mdSnu + "\t" + dN + "\t" + N);
                }
                //System.out.println("last: " + dSnu + "\t" + mdSnu + "\t" + dN + "\t" + N);
                System.out.println("------- end   integration --------------------");
                System.out.println("Number of sources: " + N + " sr^{-1}          ");
                System.out.println("----------------------------------------------");
        }


	XYSeriesCollection dataset = new XYSeriesCollection();
        //dataset.addSeries(s1);
	for (int i = 0; i < s.length; i++) {
	        dataset.addSeries(s[i]);
	}
        /*dataset.addSeries(s3);
        dataset.addSeries(s4);*/

        return dataset;
    }

	/**
	 * nu in MHz
	 */
	public static double integrand(double S1400MHz, double nu) {
		double Snu = 0;
		return Snu = Math.pow((1400/nu), 0.7) * S1400MHz;
	}

    public static JPanel createDemoPanel() {
        JFreeChart chart = createChart(createDataset());
        return new ChartPanel(chart);
    }
    
    public static void main(String[] args) {

        RadioSourceCountsLofar75MHz demo = new RadioSourceCountsLofar75MHz("Source counts");
        demo.pack();
        RefineryUtilities.centerFrameOnScreen(demo);
        demo.setVisible(true);

    }

}

