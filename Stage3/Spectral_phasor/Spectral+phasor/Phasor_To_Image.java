
import ij.*;
import ij.process.*;
import ij.gui.*;
import java.awt.*;
import ij.plugin.filter.*;
import blablab.*;

// Reciprocal analysis to go back from phasor to image
// written by Farzad Fereidouni (F.Fereidouni@uu.nl)
// version 1.1
// 2012 May 29
// It can handle irregular region of interests; commented by Arjen Bader
public class Phasor_To_Image implements PlugInFilter {

    ImagePlus imp;

    public int setup(String arg, ImagePlus imp) {
        this.imp = imp;
        return DOES_RGB;
    }

    public void run(ImageProcessor ip) {
        MetaData meta = new MetaData(imp);
          Roi roi=imp.getRoi();
        if (WindowManager.getImage(meta.getImageTitle()) != null) {

            ImagePlus imp2 = WindowManager.getImage(meta.getImageTitle());
            ImageStack ip2 = imp2.getStack();
            int K = ip2.getSize();

            double Dim_x = ip2.getWidth();
            double Dim_y = ip2.getHeight();
            double phasor_r[] = meta.getPhasorMAP_r();
            double phasor_i[] = meta.getPhasorMAP_i();
            double count, count_max = 0, getvoxel;
            double spec_t[] = new double[K + 1];
            double spec_tx[] = new double[K + 1];
            int dimension = ip2.getWidth() * ip2.getHeight();

            ImagePlus X = NewImage.createImage("X", (int) Dim_x, (int) Dim_y, 1, 32, NewImage.FILL_BLACK);
            ImageProcessor X_ip = X.getProcessor();
            for (int i = 0; i < dimension; i++) {
                if (phasor_r[i] != -2 && phasor_i[i] != -2) {
               if (roi!=null)      {
                    if(roi.contains((int)phasor_r[i],(int) phasor_i[i])){

                        count = 0;
                        for (int z = 0; z <= K; z++) {
                            getvoxel = ip2.getVoxel((int) (i - Math.floor(i / Dim_x) * Dim_x), (int) Math.floor(i / Dim_x), z);
                            spec_t[z] += getvoxel;
                            count += getvoxel;
                            spec_tx[z] = z;
                        }
                        if (count > count_max) {
                            count_max = count;
                        }
                        X_ip.setf(i, (float) count);
                    }
                }
                }
            }

            Plot Spectrum = new Plot("Spectrum", "Chanel", "Intensity", spec_tx, spec_t);
            //Spectrum.setLimits(0, K, 0, max_c);
            Spectrum.show();


            IJ.setMinAndMax(X, 0, count_max);

            X.updateAndDraw();
            X.show();

        } else {
            IJ.showMessage("The corresponding image is not found");
        }
    }
}
