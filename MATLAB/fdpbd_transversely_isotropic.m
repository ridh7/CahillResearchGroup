clearvars

%% notes

% from top to bottom:
% 3: air;
% 1: thin metal coating;
% 2: bulk material tha is transversely isotropic ("material" in short)

% "transversely isotropic" means that the material has unaxial symmetry for
% both thermal conductivity, elastic constants, and coefficient of thermal
% expansion; and that the axis is perpendicular to the sample surface

% coordinate system:
% r: in-plane
% z: through-plane

% code running time: ~ 0.1 s per frequency point


% define filenames for the data to be analyzed
FileNames_data = '68_2024-09-12_good_MT200_30k-30Hz_40P_122mV_0p6pump_0.83probe_5X';

% load the arrays for the out-of-phase signal, in-phase signal,
% ratio (-in-phase/out-of-phase), frequency, and the detector SUM voltage
[V_out_data,V_in_data,V_ratio_data,V_SUM_data,Fexp]=GetData_out_in_ratio_f_VSUM(FileNames_data);


f_amp=95e3;          % 95e3  from fit to Ni and CaF2 %145e3 for YSZ
delay_1 = 0.89e-5;   % 0.89e-5 from fit to Ni
delay_2 = -1.3e-11;  % -1.3e-11 from fit to Ni
complex_leaking = 1./(1+(1i)*Fexp/f_amp)./exp(1i*(delay_1*Fexp+delay_2*Fexp.^2));


% correct the measured data using the "leaking" data
[Vin_exp,Vout_exp,ratio]=datacorrection_complex_leaking(V_out_data,V_in_data,complex_leaking);

% Find the total number of points
num_points = length(Fexp);

% Calculate the starting and ending indices for the middle 15 points
start_idx = floor((num_points - 15) / 2) + 1;
end_idx = start_idx + 15 - 1;

% Extract the middle 20 data points
Fexp_middle = Fexp(start_idx:end_idx);
Vin_exp_middle = Vin_exp(start_idx:end_idx);
Vout_exp_middle = Vout_exp(start_idx:end_idx);
ratio_middle = ratio(start_idx:end_idx);  % Extract the ratio data


ff = logspace(log10(5e3),log10(300),40)';  % modulation frequency, (Hz)
w_rms = 11.2e-6; % rms beam radii, (m)
r_0 = 12.6e-6; % beam offset , (m)

% thermal properties of material
sigma_2_r = 0.64; % thermal conductivity in-plane
sigma_2_z = 0.21; % thermal conductivity through-plane
capac_2 = 1.56e6;  % volumetric heat capacity
rho_2 = 1430;   % density, (kg/m^3)

% elastic and thermal expansion properties of material
% transversely isotropic
alphaT_vertical = 28e-6; % linear CTE penpendicular to axis of material (i.e., in-plane), (K^(-1))
alphaT_parallel = 120e-6; % linear CTE parallel to axis of material (i.e., through-plane), (K^(-1))
%%for HN and EN 
% C11_0_2 = 8.6e9;
% C12_0_2 = 5.8e9;
% C13_0_2 = 5.8e9;
% C33_0_2 = 5.8e9;
% C44_0_2 = 1.2e9;

C11_0_2 = 8.9e9;
C12_0_2 = 5.4e9;
C13_0_2 = 5.4e9;
C33_0_2 = 5.6e9;
C44_0_2 = 2.1e9;

% % isotropic
% alphaT_vertical = 120e-6;
% alphaT_parallel = 120e-6;
% E_3 = 1.1e9; % Young's modulus
% niu_3 = 0.46;
% C11_0_2 = E_3*(1-niu_3)/(1+niu_3)/(1-2*niu_3);
% C12_0_2 = E_3*niu_3/(1+niu_3)/(1-2*niu_3);
% C13_0_2 = C12_0_2;
% C33_0_2 = C11_0_2;
% C44_0_2 = E_3/2/(1+niu_3);

%% default parameters

% laser power
incident_pump =0.69e-3;     % avarage power of digital power (square wave) pump before lens (W), set 10 mW
V_sum = 0.18; % detector sum voltage, (V)
n_al=2.9;
k_al=8.2;
lens_transmittance = 0.92; % transmittance of lens, 10x
refl_al=abs(n_al-1+(1i)*k_al)^2/abs(n_al+1+(1i)*k_al)^2;
absorbed_pump=1-refl_al;
A0 = incident_pump*lens_transmittance*4.0/pi*absorbed_pump;

% metal coating (Al) properties
L_1 = 70e-9; % thickness, (m)
sigma_1 = 129; % thermal conductivity
capac_1 = 2.42e6;
Dif_1 = sigma_1/capac_1; % thermal diffusivity
G_int = 100e6; % thermal boudnary conductance of Al/bulk material interface
C11_0_1 = 107.4e9; % elastic constant, (Pa)
C12_0_1 = 60.5e9;
C44_0_1 = 28.3e9;
rho_1 = 2.70e3;
alphaT_1 = 23.1e-6;

% air properties
sigma_3 = 0.028;
capac_3 = 1192;

% approximation factor
C_probe = 0.65;

%% derived parameters

% metal coating
beta_1 = (C11_0_1 + 2*C12_0_1)*alphaT_1;
betax_1 = beta_1;
betay_1 = beta_1;
betaz_1 = beta_1;
C11_1 = (C11_0_1 + C12_0_1 + 2*C44_0_1)/2;
C33_1 = (C11_0_1 + 2*C12_0_1 + 4*C44_0_1)/3;
C44_1 = (C11_0_1 - C12_0_1 + C44_0_1)/3;
C12_1 = (C11_0_1 + 5*C12_0_1 - 2*C44_0_1)/6;
C13_1 = (C11_0_1 + 2*C12_0_1 - 4*C44_0_1)/3;
C46_1 = 0;
C22_1 = C11_1;
C23_1 = C13_1;
C55_1 = C44_1;
C66_1 = (C11_1 - C12_1)/2;
C22C11_1 = C22_1/C11_1;
C33C11_1 = C33_1/C11_1;
C12C11_1 = C12_1/C11_1;
C13C11_1 = C13_1/C11_1;
C23C11_1 = C23_1/C11_1;
C44C11_1 = C44_1/C11_1;
C55C11_1 = C55_1/C11_1;
C66C11_1 = C66_1/C11_1;
C46C11_1 = C46_1/C11_1;
sqrtC11rho_1 = sqrt(C11_1/rho_1);
betaxC11_1 = betax_1/C11_1;
betayC11_1 = betay_1/C11_1;
betazC11_1 = betaz_1/C11_1;

% material
Dif_2 = sigma_2_z/capac_2;
betax_2 = (C11_0_2 + C12_0_2)*alphaT_vertical + C13_0_2*alphaT_parallel;
betay_2 = betax_2;
betaz_2 = 2*C13_0_2*alphaT_vertical + C33_0_2*alphaT_parallel;
C11_2 = C11_0_2;
C12_2 = C12_0_2;
C13_2 = C13_0_2;
C33_2 = C33_0_2;
C44_2 = C44_0_2;
C22_2 = C11_0_2;
C23_2 = C13_0_2;
C55_2 = C44_0_2;
C66_2 = (C11_0_2 - C12_0_2)/2;
C22C11_2 = C22_2/C11_2;
C33C11_2 = C33_2/C11_2;
C12C11_2 = C12_2/C11_2;
C13C11_2 = C13_2/C11_2;
C23C11_2 = C23_2/C11_2;
C44C11_2 = C44_2/C11_2;
C55C11_2 = C55_2/C11_2;
C66C11_2 = C66_2/C11_2;
sqrtC11rho_2 = sqrt((1+(1e-6)*(1i))*C11_2/rho_2);
betaxC11_2 = betax_2/C11_2;
betayC11_2 = betay_2/C11_2;
betazC11_2 = betaz_2/C11_2;

% air
Dif_3 = sigma_3/capac_3;

%% calculation of PBD angle

n_p = 63;
up_p = 8/w_rms;
d_p = up_p/n_p;
pp = d_p:d_p:up_p;

A_1 = zeros(6,6);
B_1 = zeros(6,6);
D_1 = zeros(6,1);
A_1(1,4) = 1;
A_1(2,5) = 1;
A_1(3,6) = 1;
A_1(4,1) = C55C11_1;
A_1(5,2) = C44C11_1;
A_1(6,3) = C33C11_1;
B_1(4,4) = 1;
B_1(5,5) = 1;
B_1(6,6) = 1;
D_1(6) = betazC11_1;

A_2 = zeros(6,6);
B_2 = zeros(6,6);
D_2 = zeros(6,1);
A_2(1,4) = 1;
A_2(2,5) = 1;
A_2(3,6) = 1;
A_2(4,1) = C55C11_2;
A_2(5,2) = C44C11_2;
A_2(6,3) = C33C11_2;
B_2(4,4) = 1;
B_2(5,5) = 1;
B_2(6,6) = 1;
D_2(6) = betazC11_2;

PBD_angle = zeros(length(ff),1);

for i_fr = 1:length(ff)
    I_p2 = zeros(n_p,1);
    omega = 2*pi*ff(i_fr);
    qn2_1 = (1i)*omega/Dif_1;
    qn2_2 = (1i)*omega/Dif_2;
    qn2_3 = (1i)*omega/Dif_3;
    for i_p = 1:n_p
        p = pp(i_p);
        flx = A0*exp(-w_rms^2*p^2/8);

        zeta_1 = sqrt(qn2_1 + p^2);
        zeta_2 = sqrt(qn2_2 + p^2*sigma_2_r/sigma_2_z);
        zeta_3 = sqrt(qn2_3 + p^2);
        zeta_1L_1 = zeta_1*L_1;
        sigma_1zeta_1 = sigma_1*zeta_1;
        sigma_2zeta_2 = sigma_2_z*zeta_2;
        sigma_3zeta_3 = sigma_3*zeta_3;

        G_d =  (sigma_2zeta_2*sinh(zeta_1L_1) + sigma_1zeta_1*cosh(zeta_1L_1) + sigma_1zeta_1*sigma_2zeta_2/G_int*cosh(zeta_1L_1))/sigma_1zeta_1;
        G_d = G_d/(sigma_2zeta_2*cosh(zeta_1L_1) + sigma_1zeta_1*sinh(zeta_1L_1) + sigma_1zeta_1*sigma_2zeta_2/G_int*sinh(zeta_1L_1));
        G_u = 1/sigma_3zeta_3;
        G = 1/(1/G_u + 1/G_d);
        theta_s = flx*G;
        theta_bs = cosh(zeta_1L_1)*theta_s + sigma_1zeta_1/G_int*sinh(zeta_1L_1)*theta_s - sinh(zeta_1L_1)*flx/sigma_1zeta_1 - cosh(zeta_1L_1)*flx/G_int;
        C_s1 = (sigma_2zeta_2/G_int*theta_bs + theta_bs - theta_s*exp(-zeta_1L_1))/(exp(zeta_1L_1) - exp(-zeta_1L_1));
        C_s2 = theta_s - C_s1;

        psi = pi/4;
        k = p*cos(psi);
        xi = p*sin(psi);

        A_1(1,1) = -C46C11_1*(1i)*k;
        A_1(2,2) = C46C11_1*(1i)*k;
        A_1(1,2) = C46C11_1*(1i)*xi;
        A_1(2,1) = C46C11_1*(1i)*xi;
        A_1(1,3) = C13C11_1*(1i)*k;
        A_1(2,3) = C23C11_1*(1i)*xi;
        B_1(1,1) = k^2 + C66C11_1*xi^2 - omega^2/sqrtC11rho_1^2;
        B_1(2,2) = C22C11_1*xi^2 + C66C11_1*k^2 - omega^2/sqrtC11rho_1^2;
        B_1(1,2) = (C12C11_1 + C66C11_1)*k*xi;
        B_1(2,1) = (C12C11_1 + C66C11_1)*k*xi;
        B_1(3,3) = -omega^2/sqrtC11rho_1^2;
        B_1(1,3) = C46C11_1*(xi^2 - k^2);
        B_1(2,3) = 2*C46C11_1*k*xi;
        B_1(3,4) = -(1i)*k;
        B_1(3,5) = -(1i)*xi;
        B_1(4,1) = C46C11_1*(1i)*k;
        B_1(4,2) = -C46C11_1*(1i)*xi;
        B_1(4,3) = -C55C11_1*(1i)*k;
        B_1(5,1) = -C46C11_1*(1i)*xi;
        B_1(5,2) = -C46C11_1*(1i)*k;
        B_1(5,3) = -C44C11_1*(1i)*xi;
        B_1(6,1) = -C13C11_1*(1i)*k;
        B_1(6,2) = -C23C11_1*(1i)*xi;
        D_1(1) = betaxC11_1*(1i)*k;
        D_1(2) = betayC11_1*(1i)*xi;
        inv_A_1 = inv(A_1);
        N_1 = inv_A_1*D_1;
        [Q_1, R_1] = eig(B_1,A_1);
        LAMBDA_1 = zeros(6,1);
        for i = 1:6
            LAMBDA_1(i) = R_1(i,i);
        end
        condi_1 = rcond(Q_1);
        if condi_1 < 2e-16
            pause;
        end
        inv_Q_1 = inv(Q_1);
        U_1 = inv_Q_1*N_1;

        A_2(1,3) = C13C11_2*(1i)*k;
        A_2(2,3) = C23C11_2*(1i)*xi;
        B_2(1,1) = k^2 + C66C11_2*xi^2 - omega^2/sqrtC11rho_2^2;
        B_2(2,2) = C22C11_2*xi^2 + C66C11_2*k^2 - omega^2/sqrtC11rho_2^2;
        B_2(1,2) = (C12C11_2 + C66C11_2)*k*xi;
        B_2(2,1) = (C12C11_2 + C66C11_2)*k*xi;
        B_2(3,3) = -omega^2/sqrtC11rho_2^2;
        B_2(3,4) = -(1i)*k;
        B_2(3,5) = -(1i)*xi;
        B_2(4,3) = -C55C11_2*(1i)*k;
        B_2(5,3) = -C44C11_2*(1i)*xi;
        B_2(6,1) = -C13C11_2*(1i)*k;
        B_2(6,2) = -C23C11_2*(1i)*xi;
        D_2(1) = betaxC11_2*(1i)*k;
        D_2(2) = betayC11_2*(1i)*xi;
        inv_A_2 = inv(A_2);
        N_2 = inv_A_2*D_2;
        [Q_raw_2, R_raw_2] = eig(B_2,A_2);
        Q_2 = zeros(6,6);
        R_2 = zeros(6,6);
        count_2 = 0;
        for i = 1:6
            if real(R_raw_2(i,i)) < 0
                count_2 = count_2 + 1;
                R_2(count_2,count_2) = R_raw_2(i,i);
                Q_2(:,count_2) = Q_raw_2(:,i);
            else
                R_2(i-count_2+3,i-count_2+3) = R_raw_2(i,i);
                Q_2(:,i-count_2+3) = Q_raw_2(:,i);
            end
        end
        LAMBDA_2 = zeros(6,1);
        for i = 1:6
            LAMBDA_2(i) = R_2(i,i);
        end
        condi_2 = rcond(Q_2);
        if condi_2 < 2e-16
            pause;
        end
        inv_Q_2 = inv(Q_2);
        U_2 = inv_Q_2*N_2;

        BCM = zeros(9,9);
        BCC = zeros(9,1);
        for i_cl = 1:6
            BCM(1:3,i_cl) = Q_1(4:6,i_cl);
            BCM(4:9,i_cl) = Q_1(1:6,i_cl)*exp(LAMBDA_1(i_cl)*L_1);
        end
        for i_cl = 7:9
            BCM(4:6,i_cl) = -Q_2(1:3,i_cl-6)*exp(LAMBDA_2(i_cl-6)*L_1);
            BCM(7:9,i_cl) = -C11_0_2/C11_1*Q_2(4:6,i_cl-6)*exp(LAMBDA_2(i_cl-6)*L_1);
        end
        for i_rw = 1:3
            sum = 0;
            for jj = 1:6
                temp = Q_1(i_rw+3,jj)*U_1(jj)*(C_s1/(zeta_1-LAMBDA_1(jj)) + C_s2/(-zeta_1-LAMBDA_1(jj)));
                sum = sum + temp;
            end
            BCC(i_rw) = -sum;
        end
        for i_rw = 4:6
            sum1 = 0;
            sum2 = 0;
            for jj = 1:6
                temp1 = Q_1(i_rw-3,jj)*U_1(jj)*(C_s1*exp(zeta_1L_1)/(zeta_1-LAMBDA_1(jj)) + C_s2*exp(-zeta_1L_1)/(-zeta_1-LAMBDA_1(jj)));
                temp2 = Q_2(i_rw-3,jj)*U_2(jj)*(theta_bs/(-zeta_2-LAMBDA_2(jj)));
                sum1 = sum1 + temp1;
                sum2 = sum2 + temp2;
            end
            BCC(i_rw) = -sum1 + sum2;
        end
        for i_rw = 7:9
            sum1 = 0;
            sum2 = 0;
            for jj = 1:6
                temp1 = Q_1(i_rw-3,jj)*U_1(jj)*(C_s1*exp(zeta_1L_1)/(zeta_1-LAMBDA_1(jj)) + C_s2*exp(-zeta_1L_1)/(-zeta_1-LAMBDA_1(jj)));
                temp2 = Q_2(i_rw-3,jj)*U_2(jj)*(theta_bs/(-zeta_2-LAMBDA_2(jj)));
                sum1 = sum1 + temp1;
                sum2 = sum2 + temp2;
            end
            BCC(i_rw) = -sum1 + (C11_0_2/C11_1)*sum2;
        end
        J = BCM\BCC;
        w_s_H = Q_1(3,1)*J(1) + Q_1(3,2)*J(2) + Q_1(3,3)*J(3) + Q_1(3,4)*J(4) + Q_1(3,5)*J(5) + Q_1(3,6)*J(6);
        sssum = 0;
        for jj = 1:6
            temp = Q_1(3,jj)*U_1(jj)*(C_s1/(zeta_1-LAMBDA_1(jj)) - C_s2/(zeta_1+LAMBDA_1(jj)));
            sssum = sssum + temp;
        end
        w_s_P = sssum;
        Z_p_omega = -(w_s_H + w_s_P);
        I_p2(i_p,1) = Z_p_omega*exp(-w_rms^2*p^2/8)*(-besselj(1,p*r_0))*p^2;

    end
    PBD_angle(i_fr,1) = C_probe/pi*simpson_inte(I_p2,d_p);
end

%% calculation of lock-in amplifier signal

PBD_signal = PBD_angle/sqrt(2)*2*37.0*V_sum;
in_phase_PBD_signal_1 = real(PBD_signal);
in_phase_PBD_signal= abs(in_phase_PBD_signal_1);
in_phase= abs(in_phase_PBD_signal);
out_of_phase_PBD_signal_1 = -1*imag(PBD_signal);
out_of_phase_PBD_signal = out_of_phase_PBD_signal_1;
ratio_PBD_signal = -in_phase_PBD_signal./out_of_phase_PBD_signal;


%% signal plotting

figure(101)
subplot(1,2,1)
semilogx(ff, in_phase_PBD_signal,'ko--','linewidth',1.5); hold on
semilogx(ff, out_of_phase_PBD_signal,'kx--','linewidth',1.5); hold on
semilogx(Fexp_middle, Vin_exp_middle, 'ro--','linewidth',1.5); hold on;
semilogx(Fexp_middle, Vout_exp_middle, 'rx--','linewidth',1.5); hold on;
hold on;
box on; axis tight;
set(gca,'linewidth',1.5,'fontsize',16,'fontname','Times New Roman');
xlabel('f (Hz)');
ylabel('in, out-of-phase (V)')
% Plot the text with the specified properties
% Create dummy points for legend
h3 = plot(nan, nan, 'r', 'DisplayName', 'Experiment');
h4 = plot(nan, nan, 'k', 'DisplayName', 'Model');
legend([h3, h4], 'Location', 'best'); % Include the dummy points in the legend
subplot(1,2,2)
loglog(ff, ratio_PBD_signal,'ko--','linewidth',1.5); hold on
semilogx(Fexp_middle, ratio_middle, 'ro--','linewidth',1.5); hold on;
box on; axis tight;
set(gca,'linewidth',1.5,'fontsize',16,'fontname','Times New Roman');
xlabel('f (Hz)');
ylabel('ratio');

%% functions

function I = simpson_inte(array,pace)
steps = length(array);
edge_sum = sum(array(3:2:steps-2));
mid_sum = sum(array(2:2:steps-1));
I = (1/6)*(2*pace)*(array(1) + 2*edge_sum + 4*mid_sum + array(steps));
end
