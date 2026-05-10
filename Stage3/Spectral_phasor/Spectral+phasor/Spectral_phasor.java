
import ij.*;
import ij.plugin.filter.PlugInFilter;
import ij.process.*;
import ij.gui.*;
import java.awt.*;
import java.util.Arrays;
import blablab.*;

// Spectral phasor 1.4
// for analysis of Spectral images
// written by Farzad Fereidouni (F.Fereidouni@uu.nl) 
// November 10, 2011
public class Spectral_phasor implements PlugInFilter {

    protected ImagePlus imp;
    private double minPxlPctl = 0.025;    // signal (percentile); intensity image is
    private double maxPxlPctl = 0.975;    // scaled to display minPxlPctl -> maxPxlPctl

    public int setup(String arg, ImagePlus imp) {
        this.imp = imp;
        return DOES_ALL + STACK_REQUIRED;
    }

    public void run(ImageProcessor ip) {
        ImageStack stack = imp.getStack();
        int dimension = ip.getWidth() * ip.getHeight();
        // takes pixels of one slice

        GenericDialog gd = new GenericDialog("Spectral Phasor");
        gd.addNumericField("Threshold:", 50, 0);
        gd.addNumericField("Back Ground :", 0, 0);
        gd.addCheckbox("Show the Spectrum?", false);
        gd.showDialog();

        if (gd.wasCanceled()) {
            return;
        }



//Region of interest
        
         Roi roi = imp.getRoi();
       // Reading the dialouge
        double threshold = (double) gd.getNextNumber();
        double back_ground = gd.getNextNumber();
        boolean show_spectrum = gd.getNextBoolean();
        int phasor_dim = 400;

        int m = 0;
        int K = stack.getSize();
// histogram min and max
        double min = 255 * 255 * 255;
        double max = 0;
//maximum count number

        double max_c = 0;
        double min_c = 1e10;
        /*Image dimensions */
       
        int Dim_x = ip.getWidth();
        int Dim_y = ip.getHeight();

     

        /*Real and imaginary parts of specs over Image */
        double sr[][] = new double[Dim_x][Dim_y];
        double si[][] = new double[Dim_x][Dim_y];

        double cx, cy;


        /*Real and imaginary parts of  crescent */
        double cr[] = new double[10000];
        double ci[] = new double[10000];


        /*Total counts of every pixiel */
        double count[][] = new double[Dim_x][Dim_y];
        double count_i[] = new double[Dim_x * Dim_y];
        /*first harmonic frequency*/
        double omega = 2.0 * Math.PI / K;
        /*The array for pixels of image*/
        // int[] pixels;
/*spec curve at every pixel*/
        double[][][] spec = new double[K + 1][Dim_x][Dim_y];
        double spec_t[] = new double[K + 1];
        double spec_tx[] = new double[K + 1];
        // phasor of each pixel
        double[] phasormap_r = new double[Dim_x * Dim_y];
        double[] phasormap_i = new double[Dim_x * Dim_y];
        double v = 0, u = 0;

        // building the spec curve for each pixel
        for (int y = 0; y < Dim_y; y++) {
            IJ.showProgress(y, Dim_y * 2);
            for (int x = 0; x < Dim_x; x++) {
                for (int i = 1; i <= K; i++) {
                    if (roi != null) {
                    if (roi.contains(x, y)) {
                    
                    spec[i][x][y] = stack.getVoxel(x , y , i - 1) - (back_ground/K);
                    if (spec[i][x][y] < 0) {
                        spec[i][x][y] = 0;
                    }
                    spec_t[i] += spec[i][x][y];
                    spec_tx[i] = i;
                    
                    }
                    }else{
                        
                    
                    
                       spec[i][x][y] = stack.getVoxel(x , y , i - 1) - (back_ground/K);
                    if (spec[i][x][y] < 0) {
                        spec[i][x][y] = 0;
                    }
                    spec_t[i] += spec[i][x][y];
                    spec_tx[i] = i; 
                    }
                }
            }
        }

        if (show_spectrum == true) {
            Plot Spectrum = new Plot("Total Spectrum-" + imp.getTitle(), "pixels", "Intensity", spec_tx, spec_t);
            //Spectrum.setLimits(0, K, 0, max_c);
            Spectrum.show();
        }
        // generating cos and sin
             double cos[] = new double[K + 1];
             double sin[] = new double[K + 1];
             
             for (int i = 1; i <= K; i++) {
             cos[i]= Math.cos(omega * (i - .5));
             sin[i]= Math.sin(omega * (i - .5));
              }
        
        
// fourier transformation of spec curve pixel by pixel
        for (int y = 0; y < Dim_y; y++) {
            IJ.showProgress(y + Dim_y, Dim_y * 2);
            for (int x = 0; x < Dim_x; x++) {
                sr[x][y] = 0;
                si[x][y] = 0;

                count[x][y] = 0;
// making the total counts per pixel
                for (int i = 1; i <= K; i++) {
                    count[x][y] += spec[i][x][y];
                }

                if (count[x][y] > threshold) {
                    count_i[x + y * Dim_x] = count[x][y];
                    for (int i = 1; i <= K; i++) {
                        //real and imaginary parts of fourier transform of spec curves
                        sr[x][y] += spec[i][x][y] * cos[i] / count[x][y];
                        si[x][y] += spec[i][x][y] * sin[i]/ count[x][y];
                    }

                }
            }
        }

//defining the zize of the phasor plot based on data
/*Phasor plot dimensions */

        Arrays.sort(count_i);
        min_c = count_i[(int) (count_i.length * minPxlPctl)];
        max_c = count_i[(int) (count_i.length * maxPxlPctl)];
        int phasor_hist[][] = new int[phasor_dim + 1][phasor_dim + 1];



// generating new image to show the phasor
        ImagePlus phasor = NewImage.createRGBImage("Phasor plot-" + imp.getTitle(), phasor_dim + 71, phasor_dim + 1,
                1, NewImage.FILL_BLACK);
        ImageProcessor ip_phasor = phasor.getProcessor();


        for (int i = 0; i < dimension; i++) {
            phasormap_r[i] = -2;
            phasormap_i[i] = -2;
        }

//coordinates for histogram
        int jx = 0;
        int jy = 0;

//filling the histogram
        for (int y = 0; y < Dim_y; y++) {
            for (int x = 0; x < Dim_x; x++) {

                if (count[x][y] > threshold) {
                    jx = (int) (phasor_dim * (sr[x][y] + 1) / 2);
                    jy = (int) (phasor_dim * (si[x][y] + 1) / 2);
                    phasormap_r[(x ) + (y ) * Dim_x] = (double) jx;
                    phasormap_i[(x ) + (y ) * Dim_x] = (double) jy;
                    //phasormap_r[x + y * Dim_x] = (double) jx;
                    //phasormap_i[x + y * Dim_x] = (double) jy;
                    phasor_hist[jx][jy] += 1;
                    if (phasor_hist[jx][jy] > max) {
                        max = phasor_hist[jx][jy];
                    }
                    if (phasor_hist[jx][jy] < min & phasor_hist[jx][jy] > 0) {
                        min = phasor_hist[jx][jy];
                    }
                }
            }
        }


        MetaData meta = new MetaData(phasor);
        meta.set(MetaData.MetaDataType.SX, Dim_x);
        meta.set(MetaData.MetaDataType.SY, Dim_y);
        meta.set(MetaData.MetaDataType.PHASORMAP_r, phasormap_r);
        meta.set(MetaData.MetaDataType.PHASORMAP_i, phasormap_i);
        meta.set(MetaData.MetaDataType.IMAGE_TITLE, imp.getTitle());

        // fourier transformation of semicircle
        
      ip_phasor.setColor(Color.pink);
      ip_phasor.moveTo((int)((Math.cos((1 - .5) * omega) + 1) * phasor_dim / 2), (int)((Math.sin((1 - .5) * omega) + 1) * phasor_dim / 2));
        for (int j = 2; j <= K; j++) {

// Real and imaginary of fourier transformation of  circle
            cr[j] = (Math.cos((j - .5) * omega) + 1) * phasor_dim / 2;
            ci[j] = (Math.sin((j - .5) * omega) + 1) * phasor_dim / 2;

//Drawing semicircle and circle
            
           ip_phasor.lineTo((int) cr[j], (int) ci[j]);

        }


        for (int y = 0; y < Dim_y; y++) {
            for (int x = 0; x < Dim_x; x++) {

                jx = (int) (phasor_dim * (sr[x][y] + 1) / 2);
                jy = (int) (phasor_dim * (si[x][y] + 1) / 2);

                if (count[x][y] > threshold) {
                    if ((phasor_hist[jx][jy] - min) / (max - min) >= 0) {
                        ip_phasor.setColor(Color.HSBtoRGB((float) ((phasor_hist[jx][jy] - min) / (max - min)), 1f, 1f));
                        ip_phasor.drawPixel(jx, jy);
                    }
                }
            }
        }
// drawing the venter
                  ip_phasor.setColor(Color.white);
      ip_phasor.fillOval(phasor_dim/2-3, phasor_dim/2-3, 6, 6);
                 ip_phasor.setColor(Color.BLACK);
        ip_phasor.drawOval(phasor_dim/2-4, phasor_dim/2-4, 7, 7);


       for (int cbar=0;cbar<phasor_dim;cbar++){
                ip_phasor.setColor(Color.HSBtoRGB((float) ((float)cbar / (float)phasor_dim*.8), 1f, 1f));
                            ip_phasor.drawLine(phasor_dim+10, phasor_dim-cbar, phasor_dim+20, phasor_dim-cbar);
            }
                        ip_phasor.moveTo(phasor_dim+25, 15);
                        ip_phasor.setColor(Color.white);
                        ip_phasor.drawString(Double.toString(max));
                        ip_phasor.moveTo(phasor_dim+25, phasor_dim);
                        ip_phasor.drawString(Double.toString((min)));

        phasor.show();
        phasor.updateAndDraw();


    }
}
