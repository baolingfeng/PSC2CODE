// g++ houghlines.cpp `pkg-config --cflags --libs opencv`

#include "opencv2/highgui/highgui.hpp"
#include "opencv2/imgproc/imgproc.hpp"

#include <iostream>

using namespace cv;
using namespace std;

#define PI 3.14159265

void help()
{
	cout << "\nThis program demonstrates line finding with the Hough transform.\n"
			"Usage: ./houghlines <image_name>, Default is pic1.jpg\n" << endl;
}

int main(int argc, char** argv)
{
	const char* filename = argc >= 2 ? argv[1] : "pic1.jpg";

	Mat src = imread(filename, 0);
	Mat demo = Mat::zeros( src.size(), CV_8U );
	if(src.empty())
	{
		help();
		cout << "can not open " << filename << endl;
		return -1;
	}

	Mat dst, cdst;
	Canny(src, dst, 50, 20, 3);
	cvtColor(dst, cdst, CV_GRAY2BGR);

	#if 0
		vector<Vec2f> lines;
		HoughLines(dst, lines, 1, CV_PI/180, 100, 0, 0 );

		for( size_t i = 0; i < lines.size(); i++ )
		{
			float rho = lines[i][0], theta = lines[i][1];
			Point pt1, pt2;
			double a = cos(theta), b = sin(theta);
			double x0 = a*rho, y0 = b*rho;
			pt1.x = cvRound(x0 + 1000*(-b));
			pt1.y = cvRound(y0 + 1000*(a));
			pt2.x = cvRound(x0 - 1000*(-b));
			pt2.y = cvRound(y0 - 1000*(a));
			line( cdst, pt1, pt2, Scalar(0,0,255), 3, CV_AA);
		}
	#else
		vector<Vec4i> lines;
		HoughLinesP(dst, lines, 1, CV_PI/180, 50, 50, 10 );
		RNG rc;
		cout.precision(2);
		for( size_t i = 0; i < lines.size(); i++ )
		{
			Vec4i l = lines[i];
			bool along_y = abs(l[1]-l[3])
						&& abs(l[0]-l[2])/float(abs(l[1]-l[3])) < sin(10*PI/180)
						&& abs(l[1]-l[3]) > 0.2*src.rows;
			bool along_x = abs(l[0]-l[2])
						&& abs(l[1]-l[3])/float(abs(l[0]-l[2])) < sin(15*PI/180)
						&& abs(l[0]-l[2]) > 0.2*src.cols;
			if (along_y || along_x) {
				// cout << endl;
				cout << l[0] << "\t" << l[1] << " | " << l[2] << "\t" << l[3] << " ... ";
				if (along_y)
					cout << "along y" << endl;
						// << abs(l[0]-l[2])/float(max(l[0], l[2])) << "\t"
						// << 0.001*max(l[1], l[3]) << endl;
				if (along_x)
					cout << "along x" << endl;
						// << abs(l[1]-l[3])/float(max(l[1], l[3])) << "\t"
						// << 0.001*max(l[0], l[2]) << endl;
				line( src, Point(l[0], l[1]), Point(l[2], l[3]),
						Scalar(rc.next()%255, rc.next()%255, rc.next()%255), 3, CV_AA);
			}
			// else line( src, Point(l[0], l[1]), Point(l[2], l[3]),
					// Scalar(rc.next()%255, rc.next()%255, rc.next()%255), 1, CV_AA);
		}
	#endif
	cout << "press any key to continue/end" << endl;
	imshow("demo", src);
	// imshow("detected lines", cdst);

	char k = waitKey();
	while (k == '`')
		k = waitKey();

	return 0;
}