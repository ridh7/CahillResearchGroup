% Front-side FD-PBD with probe reflected by Al coating sample in air

% version history (major change):
% 1. adapted from back-side code by Jinchi on Dec16 2022
% 2. updated on Apr03 2023 and then on May23 2023for yielding correct value of coefficient of
% thermal expansion and steady-state temperature rise
% 3. this version: the leaking data file is no longer needed as input; the signal
% data file should have an additional column for V_SUM

close all;
clearvars;

%  ======================== data files ===============================

% define filenames for the data to be analyzed
FileNames_data = '1_CaF2_176mV-100k-100Hz_40P_1pump_0p85probe_5X';

% load the arrays for the out-of-phase signal, in-phase signal,
% ratio (-in-phase/out-of-phase), frequency, and the detector SUM voltage
[V_out_data,V_in_data,V_ratio_data,V_SUM_data,f1]=GetData_out_in_ratio_f_VSUM(FileNames_data);

% calcualte the "leaking" data for correction of the frequency response due
% to the imperfection of pump modulation and detector response
% scale_leaking = 0.9762;
% f_leaking_1 = 113.9e3;
% f_leaking_2 = 199.0e3;
% complex_leaking = scale_leaking./(1+(1i)*f1/f_leaking_1)./(1+(1i)*f1/f_leaking_2);

f_amp=95e3;          % 95e3  from fit to Ni and CaF2 %145e3 for YSZ
delay_1 = 0.89e-5;   % 0.89e-5 from fit to Ni
delay_2 = -1.3e-11;  % -1.3e-11 from fit to Ni
complex_leaking = 1./(1+(1i)*f1/f_amp)./exp(1i*(delay_1*f1+delay_2*f1.^2));


% correct the measured data using the "leaking" data
[Vcorrected_in1,Vcorrected_out1,Vcorrected_ratio1]=datacorrection_complex_leaking(V_out_data,V_in_data,complex_leaking);

% calculat the average detector SUM voltage
V_SUM_avg = mean(V_SUM_data);

% ===================   sample parameters ================================

% down parameters: Al film/ interface/ material to measure

% % YSZ
% lambda_down=[150 0.1 2.2];           % thermal conductivity (W/m-K) in the surface normal direction
% eta_down=[1 1 1];                     % anisotropy of thermal conductivity; eta=kx/ky; kx is in-plane; ky is surface normal direction
% C_down=[2.44 0.1 3.0]*1e6;           % specific heat (J/m^3-K)
% h_down=[70 1 1e6]*1e-9;               % thickness (m)
% niu = 0.26; % Poisson's ratio of the material to meausre
% alphaT = 18.85e-6; % coefficient of thermal expansion of the material to meausre

%CaF2
lambda_down=[149 0.1 9.7];           % thermal conductivity (W/m-K) in the surface normal direction
eta_down=[1 1 1];                     % anisotropy of thermal conductivity; eta=kx/ky; kx is in-plane; ky is surface normal direction
C_down=[2.44 0.1 2.73]*1e6;           % specific heat (J/m^3-K)
h_down=[70 1 1e6]*1e-9;               % thickness (m)
niu = 0.26; % Poisson's ratio of the material to meausre
alphaT = 18.85e-6; % coefficient of thermal expansion of the material to meausre
% 
% % material
% lambda_down=[150 0.1 60];           % thermal conductivity (W/m-K) in the surface normal direction
% eta_down=[1 1 1];                     % anisotropy of thermal conductivity; eta=kx/ky; kx is in-plane; ky is surface normal direction
% C_down=[2.44 0.1 1.71]*1e6;           % specific heat (J/m^3-K)
% h_down=[1 1 1e6]*1e-9;               % thickness (m)
% niu = 0.26; % Poisson's ratio of the material to meausre
% alphaT = 18.85e-6; % coefficient of thermal expansion of the material to meausre


% up parameter: air
lambda_up=0.028;   % air thermal conductivity (W/m-K) in surface normal direction
eta_up=1.0;        % anisotropy of thermal conductivity, eta=kx/ky  kx is in-plane; ky is surface normal direction
C_up=1192;         % air volumetric heat capacity
h_up=1e-3;         % thickness (m) of sample; set to large value; not used in current version of code

% ========================  experimental parameters ======================

r_rms=11.20e-6;     % root-mean-square pump and probe beam 1/e^2 radius, 10x lens    
xoffset=12.6e-6;    % Beam offset (m); pump beam moved downwards by settting 13um move of the gimbal mount
r_pump=r_rms;
r_probe=r_rms;

incident_pump=1.06e-3;     % avarage power of digital power (square wave) pump before lens (W), set 10mW
incident_probe=0.85e-3;    % laser power of cw probe  before lens(W), set 10mW
n_al=2.9;                % complex optical index for Al at 780 nm from David
lens_transmittance = 0.93; % transmittance of lens, 10x
k_al=8.2;
refl_al=abs(n_al-1+(1i)*k_al)^2/abs(n_al+1+(1i)*k_al)^2;
absorbed_pump=1-refl_al;

A_pump=incident_pump*lens_transmittance*4.0/pi*absorbed_pump;
A_dc=(incident_pump+incident_probe)*absorbed_pump;
coef = alphaT*2*37.0*V_SUM_avg/sqrt(2); % for 10x only

% calculate the steady state heating
T_ss_heat = 2*pi*ss_heat(lambda_down,C_down,h_down,eta_down,lambda_up,C_up,h_up,eta_up,r_pump,r_probe,A_dc);

% ======================  fitting ===========================
% finding out-of-phase peak fc and determine frequency range of fitting (fc/10 to fc*10)
BBB = sortrows([abs(Vcorrected_out1) f1]);
fc = BBB(length(f1),2);
highlim = 0;
lowlim = 0;
for i_fr = 1:length(f1)
    f_temp = f1(i_fr);
    if f_temp<fc/10
        lowlim = lowlim + 1;
    else
        if f_temp>fc*10
            highlim = highlim + 1;
        end
    end
end

f = f1(1+highlim:length(f1)-lowlim);
Vcorrected_in=Vcorrected_in1(1+highlim:length(f1)-lowlim);
Vcorrected_out=Vcorrected_out1(1+highlim:length(f1)-lowlim);
Vcorrected_ratio=Vcorrected_ratio1(1+highlim:length(f1)-lowlim);

% toggles that select the type of fitting to do; 

   % fitting1 fits lambda of bulk sample using inphase_and_outofphase
   % fitting2 fits lambda  of bulk sample using ratio

FDPBD_fitting1=1;
FDPBD_fitting2=0;

% dgc note: changed weightings for in-phase and out-of-phase simultaneous
% fitting to weight the out-of-phase signal a fixed factor of 3 more than the in-phase
% signal. In other words, for calculating the residual, the in-phase difference between data and model is divided by
% 3*max(Vin) and the out-of-phase difference between data and model is divided by max(Vin)

flag_save = 0; % 1 if need to save data

if FDPBD_fitting1==1

% this fitting approach written by Jingyi Zhou in September 2022

f2=[f,f];
Xguess=[lambda_down(3),coef];
lb=[0,-100];   % set lower bounds to fitting parameters
ub=[100,100];  % set upper bounds to fitting parameters

Vcorrected_inn=Vcorrected_in/3.0/(max(abs(Vcorrected_in)));
Vcorrected_outn=Vcorrected_out/(max(abs(Vcorrected_in)));
Vcorrected=[Vcorrected_outn,Vcorrected_inn];
options = optimoptions('lsqcurvefit','Algorithm','levenberg-marquardt');
[Xsol,resnorm,residual,exitflag,output,lambda,J]=lsqcurvefit(@(X,f2) FDTR_FIT_inout(X,Vcorrected_in,Vcorrected_out, ...
    niu,f2,lambda_down,C_down,h_down,eta_down,lambda_up,C_up,h_up,eta_up,r_pump,r_probe,A_pump,xoffset),Xguess,f2,Vcorrected,lb,ub,options);
confidenceinterval95=nlparci(Xsol,residual,'jacobian',J)

lambda_down(3)=Xsol(1);   % reset the experimental parameters to the fitted values
coef = Xsol(2);
lambda_measure = lambda_down(3)
alphaT = Xsol(2)./(2*37*V_SUM_avg/sqrt(2))   %  37 for 10x objective, 74 for 5x objective

end

if FDPBD_fitting2==1

Xguess=lambda_down(3);
Xsol=lsqcurvefit(@(X,f) FDTR_FIT_ratio(X,Vcorrected_ratio, ...
    niu,f,lambda_down,C_down,h_down,eta_down,lambda_up,C_up,h_up,eta_up,r_pump,r_probe,A_pump,xoffset),Xguess,f,Vcorrected_ratio);

lambda_down(3)=Xsol;   % reset the experimental parameters to the fitted values
lambda_measure = lambda_down(3)

end

delta_Theta=delta_BO_Theta(niu,coef,f,lambda_down,C_down,h_down,eta_down,lambda_up,C_up,h_up,eta_up,r_pump,r_probe,A_pump,xoffset);
delta_outofphase=imag(delta_Theta);
delta_inphase=real(delta_Theta);
delta_ratio=-delta_inphase./delta_outofphase;

% plot data and fitted results
% note: if fitting ratio, the amplitude of fitted of in,out-phase data is
% like to mismatch that of data

figure(100)
subplot(1,2,1)
semilogx(f, Vcorrected_in,'ko','linewidth',1.5); hold on
semilogx(f,Vcorrected_out,'ko','linewidth',1.5); hold on
semilogx(f, delta_inphase,'b-','linewidth',1.5); hold on
semilogx(f,delta_outofphase,'b-','linewidth',1.5); hold on
box on; axis tight;
set(gca,'linewidth',1.5,'fontsize',16,'fontname','Times New Roman');
xlabel('f (Hz)');
ylabel('in, out-of-phase (V)')

subplot(1,2,2)
loglog(f, Vcorrected_ratio,'ko','linewidth',1.5); hold on
loglog(f, delta_ratio,'b-','linewidth',1.5); hold on
box on; axis tight;
set(gca,'linewidth',1.5,'fontsize',16,'fontname','Times New Roman');
xlabel('f (Hz)');
ylabel('ratio')

% write data and model to a file test.dat
if flag_save == 1
    fileID = fopen('test.dat','w');
    fprintf(fileID,'%12.3e %12.3e %12.3e %12.3e %12.3e %12.3e %12.3e %12.3e\n', [f, V_SUM_data, Vcorrected_in, Vcorrected_out, ...
        Vcorrected_ratio, delta_inphase, delta_outofphase, delta_ratio]');
    fclose(fileID);
end

% title('CaF_2: k = 9.46 W/m-K, \alpha_T = 18.9e-6 /K (w_m_s_e = 7.8 \mum, r_0 = 8.8 \mum)')