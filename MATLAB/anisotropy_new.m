% thermoelastic_model.m
% Simulates thermoelastic response of a thin metal-coated anisotropic material
% under laser-induced heating, calculates probe beam deflection, and compares
% with experimental data.

clearvars

%% Main script
function thermoelastic_model()
    % Define constants and filenames
    constants = define_constants();
    filenames = define_filenames();

    % Load and preprocess experimental data
    exp_data = load_experimental_data(filenames, constants);

    % Define material and laser parameters
    params = define_parameters(exp_data.V_SUM_avg, constants);

    % Calculate surface displacement
    Z_p_psi_omega = calculate_surface_displacement(params, constants);
    % fprintf('MATLAB Z_p_psi_omega values at selected indices:\n');
    % indices = [1, 1, 1; 1, 1, 6; 11, 11, 3];
    % for i = 1:size(indices, 1)
    %     i_p = indices(i, 1); i_psi = indices(i, 2); i_fr = indices(i, 3);
    %     z_val = Z_p_psi_omega(i_p, i_psi, i_fr);
    %     fprintf('  Z_p_psi_omega[%d,%d,%d] (freq %.2f Hz): real: %.6e, imag: %.6e, abs: %.6e\n', ...
    %             i_p, i_psi, i_fr, params.ff(i_fr), real(z_val), imag(z_val), abs(z_val));
    % end

    % Calculate probe beam deflection angle
    PBD_angle = calculate_probe_beam_deflection(Z_p_psi_omega, params, constants);
    % fprintf('MATLAB PBD_angle imaginary parts:\n');
    % disp(imag(PBD_angle));
    % fprintf('MATLAB PBD_angle magnitudes:\n');
    % disp(abs(PBD_angle));
    % fprintf('MATLAB PBD_angle at each frequency:\n');
    % for i = 1:length(params.ff)
    %     fprintf('  Freq: %.2f Hz, imag: %.6e, abs: %.6e\n', ...
    %             params.ff(i), imag(PBD_angle(i)), abs(PBD_angle(i)));
    % end

    % Calculate lock-in amplifier signals
    signals = calculate_lockin_signals(PBD_angle, exp_data.V_SUM_avg, constants);
    % fprintf('MATLAB signals.out_of_phase values:\n');
    % disp(signals.out_of_phase);
    % fprintf('Any negative signals.out_of_phase values: %d\n', any(signals.out_of_phase < 0));
    % fprintf('MATLAB signals.out_of_phase at each frequency:\n');
    % for i = 1:length(params.ff)
    %     fprintf('  Freq: %.2f Hz, out_of_phase: %.6e\n', params.ff(i), signals.out_of_phase(i));
    % end

    % Analyze signals
    analysis = analyze_signals(signals, params.ff);

    % Plot results
    plot_results(params.ff, signals, exp_data, analysis);
end

%% Helper Functions

function constants = define_constants()
    % Define constant parameters
    constants.f_amp = 95e3;          % Frequency amplitude (Hz)
    constants.delay_1 = 0.89e-5;     % Delay parameter 1 (s)
    constants.delay_2 = -1.3e-11;    % Delay parameter 2 (s^2)
    constants.lens_transmittance = 0.82; % Lens transmittance
    constants.n_al = 2.9;            % Refractive index of Al at 780 nm
    constants.k_al = 8.2;            % Extinction coefficient of Al
    constants.C_probe = 0.7;         % Probe beam correction factor
    constants.n_p = 63;              % Number of p points
    constants.n_psi = 45;            % Number of psi points
end

function filenames = define_filenames()
    % Define data filenames
    filenames.data = '103_Mylar_machine_vertical_12um_145mV-100k-100Hz_40P_20X_0p65pump_0p83probe';
end

function exp_data = load_experimental_data(filenames, constants)
    % Load experimental data
    [V_out_data, V_in_data, V_ratio_data, V_SUM_data, Fexp] = ...
        GetData_out_in_ratio_f_VSUM(filenames.data);

    % Calculate complex leaking correction
    complex_leaking = 1 ./ (1 + 1i * Fexp / constants.f_amp) ./ ...
        exp(1i * (constants.delay_1 * Fexp + constants.delay_2 * Fexp.^2));

    % Correct measured data
    [Vin_exp, Vout_exp, ratio] = datacorrection_complex_leaking(...
        V_out_data, V_in_data, complex_leaking);

    % Calculate average detector SUM voltage
    V_SUM_avg = mean(V_SUM_data);

    % Store in struct
    exp_data.V_out_data = V_out_data;
    exp_data.V_in_data = V_in_data;
    exp_data.V_ratio_data = V_ratio_data;
    exp_data.V_SUM_data = V_SUM_data;
    exp_data.Fexp = Fexp;
    exp_data.Vin_exp = Vin_exp;
    exp_data.Vout_exp = Vout_exp;
    exp_data.ratio = ratio;
    exp_data.V_SUM_avg = V_SUM_avg;
    exp_data.complex_leaking = complex_leaking;
end

function params = define_parameters(V_SUM_avg, constants)
    % Define frequency array
    % ff = logspace(log10(100e3), log10(1000), 10)'; % Vertical
    ff = logspace(log10(100e3), log10(100), 10)'; % Horizontal

    % Beam parameters
    beam.w_rms = 11.3e-6 * 0.25; % RMS beam radii (m)
    beam.r_0 = 12.6e-6 * 0.25;   % Beam offset (m)
    % beam.phi = deg2rad(90);    % Vertical/machine
    beam.phi = deg2rad(0);       % Horizontal/transverse

    % Laser power
    laser.incident_pump = 0.65e-3; % Pump power (W)
    laser.V_sum = V_SUM_avg;       % Detector sum voltage (V)
    refl_al = abs(constants.n_al - 1 + 1i * constants.k_al)^2 / ...
              abs(constants.n_al + 1 + 1i * constants.k_al)^2;
    laser.absorbed_pump = 1 - refl_al;
    laser.A0 = laser.incident_pump * constants.lens_transmittance * ...
               4.0 / pi * laser.absorbed_pump;

    % Material 1: Metal coating (Al)
    mat1.L_1 = 80e-9;           % Thickness (m)
    mat1.sigma_1 = 109;         % Thermal conductivity (W/m·K)
    mat1.capac_1 = 2.42e6;      % Volumetric heat capacity (J/m^3·K)
    mat1.Dif_1 = mat1.sigma_1 / mat1.capac_1; % Thermal diffusivity (m^2/s)
    mat1.G_int = 100e6;         % Thermal boundary conductance (W/m^2·K)
    mat1.C11_0_1 = 107.4e9;     % Elastic constants (Pa)
    mat1.C12_0_1 = 60.5e9;
    mat1.C44_0_1 = 28.3e9;
    mat1.rho_1 = 2.70e3;        % Density (kg/m^3)
    mat1.alphaT_1 = 23.1e-6;    % CTE (K^-1)

    % Material 2: Bulk material with uniaxial anisotropy
    mat2.sigma_2_x = 0.3;       % Thermal conductivity x (W/m·K)
    mat2.sigma_2_y = 0.5;       % Thermal conductivity y (W/m·K)
    mat2.sigma_2_z = mat2.sigma_2_x;
    mat2.capac_2 = 1.59e6;      % Volumetric heat capacity (J/m^3·K)
    mat2.rho_2 = 1380;          % Density (kg/m^3)
    mat2.alphaT_vertical = 70e-6;  % CTE perpendicular (K^-1)
    mat2.alphaT_parallel = 60e-6;  % CTE parallel (K^-1)
    mat2.C11_0_2 = 12.11e9;     % Elastic constants (Pa)
    mat2.C12_0_2 = 5.06e9;
    mat2.C13_0_2 = 5.68e9;
    mat2.C33_0_2 = 7.06e9;
    mat2.C44_0_2 = 1.2e9;

    % Material 3: Air
    mat3.sigma_3 = 0.028;       % Thermal conductivity (W/m·K)
    mat3.capac_3 = 1192;        % Volumetric heat capacity (J/m^3·K)
    mat3.Dif_3 = mat3.sigma_3 / mat3.capac_3; % Thermal diffusivity (m^2/s)

    % Derived parameters for material 1 (Al)
    mat1.beta_1 = (mat1.C11_0_1 + 2 * mat1.C12_0_1) * mat1.alphaT_1;
    mat1.betax_1 = mat1.beta_1;
    mat1.betay_1 = mat1.beta_1;
    mat1.betaz_1 = mat1.beta_1;
    mat1.C11_1 = (mat1.C11_0_1 + mat1.C12_0_1 + 2 * mat1.C44_0_1) / 2;
    mat1.C33_1 = (mat1.C11_0_1 + 2 * mat1.C12_0_1 + 4 * mat1.C44_0_1) / 3;
    mat1.C44_1 = (mat1.C11_0_1 - mat1.C12_0_1 + mat1.C44_0_1) / 3;
    mat1.C12_1 = (mat1.C11_0_1 + 5 * mat1.C12_0_1 - 2 * mat1.C44_0_1) / 6;
    mat1.C13_1 = (mat1.C11_0_1 + 2 * mat1.C12_0_1 - 4 * mat1.C44_0_1) / 3;
    mat1.C46_1 = 0;
    mat1.C22_1 = mat1.C11_1;
    mat1.C23_1 = mat1.C13_1;
    mat1.C55_1 = mat1.C44_1;
    mat1.C66_1 = (mat1.C11_1 - mat1.C12_1) / 2;
    mat1.C22C11_1 = mat1.C22_1 / mat1.C11_1;
    mat1.C33C11_1 = mat1.C33_1 / mat1.C11_1;
    mat1.C12C11_1 = mat1.C12_1 / mat1.C11_1;
    mat1.C13C11_1 = mat1.C13_1 / mat1.C11_1;
    mat1.C23C11_1 = mat1.C23_1 / mat1.C11_1;
    mat1.C44C11_1 = mat1.C44_1 / mat1.C11_1;
    mat1.C55C11_1 = mat1.C55_1 / mat1.C11_1;
    mat1.C66C11_1 = mat1.C66_1 / mat1.C11_1;
    mat1.C46C11_1 = mat1.C46_1 / mat1.C11_1;
    mat1.sqrtC11rho_1 = sqrt(mat1.C11_1 / mat1.rho_1);
    mat1.betaxC11_1 = mat1.betax_1 / mat1.C11_1;
    mat1.betayC11_1 = mat1.betay_1 / mat1.C11_1;
    mat1.betazC11_1 = mat1.betaz_1 / mat1.C11_1;

    % Derived parameters for material 2
    mat2.Dif_2 = mat2.sigma_2_z / mat2.capac_2;
    mat2.betax_2 = (mat2.C11_0_2 + mat2.C12_0_2) * mat2.alphaT_vertical + ...
                   mat2.C13_0_2 * mat2.alphaT_parallel;
    mat2.betay_2 = 2 * mat2.C13_0_2 * mat2.alphaT_vertical + ...
                   mat2.C33_0_2 * mat2.alphaT_parallel;
    mat2.betaz_2 = mat2.betax_2;
    mat2.C11_2 = mat2.C11_0_2;
    mat2.C22_2 = mat2.C33_0_2;
    mat2.C33_2 = mat2.C11_0_2;
    mat2.C12_2 = mat2.C13_0_2;
    mat2.C13_2 = mat2.C12_0_2;
    mat2.C23_2 = mat2.C13_0_2;
    mat2.C44_2 = mat2.C44_0_2;
    mat2.C55_2 = (mat2.C11_0_2 - mat2.C12_0_2) / 2;
    mat2.C66_2 = mat2.C44_0_2;
    mat2.C22C11_2 = mat2.C22_2 / mat2.C11_2;
    mat2.C33C11_2 = mat2.C33_2 / mat2.C11_2;
    mat2.C12C11_2 = mat2.C12_2 / mat2.C11_2;
    mat2.C13C11_2 = mat2.C13_2 / mat2.C11_2;
    mat2.C23C11_2 = mat2.C23_2 / mat2.C11_2;
    mat2.C44C11_2 = mat2.C44_2 / mat2.C11_2;
    mat2.C55C11_2 = mat2.C55_2 / mat2.C11_2;
    mat2.C66C11_2 = mat2.C66_2 / mat2.C11_2;
    mat2.sqrtC11rho_2 = sqrt((1 + 1e-6 * 1i) * mat2.C11_2 / mat2.rho_2);
    mat2.betaxC11_2 = mat2.betax_2 / mat2.C11_2;
    mat2.betayC11_2 = mat2.betay_2 / mat2.C11_2;
    mat2.betazC11_2 = mat2.betaz_2 / mat2.C11_2;

    % Store in params struct
    params.ff = ff;
    params.beam = beam;
    params.laser = laser;
    params.mat1 = mat1;
    params.mat2 = mat2;
    params.mat3 = mat3;
end

function Z_p_psi_omega = calculate_surface_displacement(params, constants)
    % Initialize arrays
    n_p = constants.n_p;
    n_psi = constants.n_psi;
    ff = params.ff;
    w_rms = params.beam.w_rms;
    up_p = 8 / w_rms;
    d_p = up_p / n_p;
    pp = d_p:d_p:up_p;
    up_psi = pi / 2;
    d_psi = up_psi / n_psi;
    ppsi = 0:d_psi:up_psi;
    Z_p_psi_omega = zeros(n_p, n_psi, length(ff));

    % Initialize matrices
    A_1 = zeros(6, 6);
    B_1 = zeros(6, 6);
    D_1 = zeros(6, 1);
    A_1(1,4) = 1; A_1(2,5) = 1; A_1(3,6) = 1;
    A_1(4,1) = params.mat1.C55C11_1;
    A_1(5,2) = params.mat1.C44C11_1;
    A_1(6,3) = params.mat1.C33C11_1;
    B_1(4,4) = 1; B_1(5,5) = 1; B_1(6,6) = 1;
    D_1(6) = params.mat1.betazC11_1;

    A_2 = zeros(6, 6);
    B_2 = zeros(6, 6);
    D_2 = zeros(6, 1);
    A_2(1,4) = 1; A_2(2,5) = 1; A_2(3,6) = 1;
    A_2(4,1) = params.mat2.C55C11_2;
    A_2(5,2) = params.mat2.C44C11_2;
    A_2(6,3) = params.mat2.C33C11_2;
    B_2(4,4) = 1; B_2(5,5) = 1; B_2(6,6) = 1;
    D_2(6) = params.mat2.betazC11_2;

    % Loop over frequencies
    for i_fr = 1:length(ff)
        omega = 2 * pi * ff(i_fr);
        qn2_1 = 1i * omega / params.mat1.Dif_1;
        qn2_2 = 1i * omega / params.mat2.Dif_2;
        qn2_3 = 1i * omega / params.mat3.Dif_3;

        for i_p = 1:n_p
            p = pp(i_p);
            flx = params.laser.A0 * exp(-w_rms^2 * p^2 / 8);

            for i_psi = 1:n_psi
                psi = ppsi(i_psi);
                k = p * cos(psi);
                xi = p * sin(psi);
                zeta_1 = sqrt(qn2_1 + p^2);
                zeta_2 = sqrt(qn2_2 + k^2 * params.mat2.sigma_2_x / params.mat2.sigma_2_z + ...
                             xi^2 * params.mat2.sigma_2_y / params.mat2.sigma_2_z);
                zeta_3 = sqrt(qn2_3 + p^2);
                zeta_1L_1 = zeta_1 * params.mat1.L_1;
                sigma_1zeta_1 = params.mat1.sigma_1 * zeta_1;
                sigma_2zeta_2 = params.mat2.sigma_2_z * zeta_2;
                sigma_3zeta_3 = params.mat3.sigma_3 * zeta_3;

                % Thermal calculations
                G_d = (sigma_2zeta_2 * sinh(zeta_1L_1) + sigma_1zeta_1 * cosh(zeta_1L_1) + ...
                       sigma_1zeta_1 * sigma_2zeta_2 / params.mat1.G_int * cosh(zeta_1L_1)) / sigma_1zeta_1;
                G_d = G_d / (sigma_2zeta_2 * cosh(zeta_1L_1) + sigma_1zeta_1 * sinh(zeta_1L_1) + ...
                             sigma_1zeta_1 * sigma_2zeta_2 / params.mat1.G_int * sinh(zeta_1L_1));
                G_u = 1 / sigma_3zeta_3;
                G = 1 / (1 / G_u + 1 / G_d);
                theta_s = flx * G;
                theta_bs = cosh(zeta_1L_1) * theta_s + sigma_1zeta_1 / params.mat1.G_int * ...
                           sinh(zeta_1L_1) * theta_s - sinh(zeta_1L_1) * flx / sigma_1zeta_1 - ...
                           cosh(zeta_1L_1) * flx / params.mat1.G_int;
                C_s1 = (sigma_2zeta_2 / params.mat1.G_int * theta_bs + theta_bs - ...
                        theta_s * exp(-zeta_1L_1)) / (exp(zeta_1L_1) - exp(-zeta_1L_1));
                C_s2 = theta_s - C_s1;

                % Material 1 matrices
                A_1(1,1) = -params.mat1.C46C11_1 * 1i * k;
                A_1(2,2) = params.mat1.C46C11_1 * 1i * k;
                A_1(1,2) = params.mat1.C46C11_1 * 1i * xi;
                A_1(2,1) = params.mat1.C46C11_1 * 1i * xi;
                A_1(1,3) = params.mat1.C13C11_1 * 1i * k;
                A_1(2,3) = params.mat1.C23C11_1 * 1i * xi;
                B_1(1,1) = k^2 + params.mat1.C66C11_1 * xi^2 - omega^2 / params.mat1.sqrtC11rho_1^2;
                B_1(2,2) = params.mat1.C22C11_1 * xi^2 + params.mat1.C66C11_1 * k^2 - ...
                           omega^2 / params.mat1.sqrtC11rho_1^2;
                B_1(1,2) = (params.mat1.C12C11_1 + params.mat1.C66C11_1) * k * xi;
                B_1(2,1) = (params.mat1.C12C11_1 + params.mat1.C66C11_1) * k * xi;
                B_1(3,3) = -omega^2 / params.mat1.sqrtC11rho_1^2;
                B_1(1,3) = params.mat1.C46C11_1 * (xi^2 - k^2);
                B_1(2,3) = 2 * params.mat1.C46C11_1 * k * xi;
                B_1(3,4) = -1i * k;
                B_1(3,5) = -1i * xi;
                B_1(4,1) = params.mat1.C46C11_1 * 1i * k;
                B_1(4,2) = -params.mat1.C46C11_1 * 1i * xi;
                B_1(4,3) = -params.mat1.C55C11_1 * 1i * k;
                B_1(5,1) = -params.mat1.C46C11_1 * 1i * xi;
                B_1(5,2) = -params.mat1.C46C11_1 * 1i * k;
                B_1(5,3) = -params.mat1.C44C11_1 * 1i * xi;
                B_1(6,1) = -params.mat1.C13C11_1 * 1i * k;
                B_1(6,2) = -params.mat1.C23C11_1 * 1i * xi;
                D_1(1) = params.mat1.betaxC11_1 * 1i * k;
                D_1(2) = params.mat1.betayC11_1 * 1i * xi;
                inv_A_1 = inv(A_1);
                N_1 = inv_A_1 * D_1;
                [Q_1, R_1] = eig(B_1, A_1);
                if i_p == 1 && i_psi == 1 && i_fr == 1
                    fprintf('MATLAB Q_1 at Z_p_psi_omega[1,1,1] (freq %.2f Hz):\n', ff(i_fr));
                    for r = 1:6
                        fprintf('  Q_1(%d,:): real: [', r);
                        fprintf('%.6e, ', real(Q_1(r,:)));
                        fprintf('], imag: [');
                        fprintf('%.6e, ', imag(Q_1(r,:)));
                        fprintf(']\n');
                    end
                end
                LAMBDA_1 = zeros(6, 1);
                for i = 1:6
                    LAMBDA_1(i) = R_1(i, i);
                end
                condi_1 = rcond(Q_1);
                if condi_1 < 2e-16
                    pause;
                end
                inv_Q_1 = inv(Q_1);
                U_1 = inv_Q_1 * N_1;

                % Material 2 matrices
                A_2(1,3) = params.mat2.C13C11_2 * 1i * k;
                A_2(2,3) = params.mat2.C23C11_2 * 1i * xi;
                B_2(1,1) = k^2 + params.mat2.C66C11_2 * xi^2 - omega^2 / params.mat2.sqrtC11rho_2^2;
                B_2(2,2) = params.mat2.C22C11_2 * xi^2 + params.mat2.C66C11_2 * k^2 - ...
                           omega^2 / params.mat2.sqrtC11rho_2^2;
                B_2(1,2) = (params.mat2.C12C11_2 + params.mat2.C66C11_2) * k * xi;
                B_2(2,1) = (params.mat2.C12C11_2 + params.mat2.C66C11_2) * k * xi;
                B_2(3,3) = -omega^2 / params.mat2.sqrtC11rho_2^2;
                B_2(3,4) = -1i * k;
                B_2(3,5) = -1i * xi;
                B_2(4,3) = -params.mat2.C55C11_2 * 1i * k;
                B_2(5,3) = -params.mat2.C44C11_2 * 1i * xi;
                B_2(6,1) = -params.mat2.C13C11_2 * 1i * k;
                B_2(6,2) = -params.mat2.C23C11_2 * 1i * xi;
                D_2(1) = params.mat2.betaxC11_2 * 1i * k;
                D_2(2) = params.mat2.betayC11_2 * 1i * xi;
                inv_A_2 = inv(A_2);
                N_2 = inv_A_2 * D_2;
                [Q_raw_2, R_raw_2] = eig(B_2, A_2);
                Q_2 = zeros(6, 6);
                R_2 = zeros(6, 6);
                count_2 = 0;
                for i = 1:6
                    if real(R_raw_2(i, i)) < 0
                        count_2 = count_2 + 1;
                        R_2(count_2, count_2) = R_raw_2(i, i);
                        Q_2(:, count_2) = Q_raw_2(:, i);
                    else
                        R_2(i - count_2 + 3, i - count_2 + 3) = R_raw_2(i, i);
                        Q_2(:, i - count_2 + 3) = Q_raw_2(:, i);
                    end
                end
                LAMBDA_2 = zeros(6, 1);
                for i = 1:6
                    LAMBDA_2(i) = R_2(i, i);
                end
                % if i_p == 1 && i_psi == 1 && i_fr == 1
                %     fprintf('MATLAB eigenvalues for Q2 at Z_p_psi_omega[1,1,1] (freq %.2f Hz):\n', ff(i_fr));
                %     fprintf('  Raw R_raw_2 diagonal:\n');
                %     for i = 1:6
                %         fprintf('    R_raw_2(%d,%d): real: %.6e, imag: %.6e, abs: %.6e\n', ...
                %                 i, i, real(R_raw_2(i,i)), imag(R_raw_2(i,i)), abs(R_raw_2(i,i)));
                %     end
                %     fprintf('  Reordered LAMBDA_2:\n');
                %     for i = 1:6
                %         fprintf('    LAMBDA_2(%d): real: %.6e, imag: %.6e, abs: %.6e\n', ...
                %                 i, real(LAMBDA_2(i)), imag(LAMBDA_2(i)), abs(LAMBDA_2(i)));
                %     end
                %     fprintf('  Implied ordering indices (1-based):\n');
                %     idx_order = zeros(6,1);
                %     count_2 = 0;
                %     for i = 1:6
                %         if real(R_raw_2(i,i)) < 0
                %             count_2 = count_2 + 1;
                %             idx_order(count_2) = i;
                %         else
                %             idx_order(i - count_2 + 3) = i;
                %         end
                %     end
                %     fprintf('    idx_order: ');
                %     fprintf('%d ', idx_order);
                %     fprintf('\n');
                % end
                condi_2 = rcond(Q_2);
                if condi_2 < 2e-16
                    pause;
                end
                inv_Q_2 = inv(Q_2);
                U_2 = inv_Q_2 * N_2;

                % Boundary conditions
                BCM = zeros(9, 9);
                BCC = zeros(9, 1);
                for i_cl = 1:6
                    BCM(1:3, i_cl) = Q_1(4:6, i_cl);
                    BCM(4:9, i_cl) = Q_1(1:6, i_cl) * exp(LAMBDA_1(i_cl) * params.mat1.L_1);
                end
                for i_cl = 7:9
                    BCM(4:6, i_cl) = -Q_2(1:3, i_cl - 6) * exp(LAMBDA_2(i_cl - 6) * params.mat1.L_1);
                    BCM(7:9, i_cl) = -params.mat2.C11_0_2 / params.mat1.C11_1 * ...
                                     Q_2(4:6, i_cl - 6) * exp(LAMBDA_2(i_cl - 6) * params.mat1.L_1);
                end
                for i_rw = 1:3
                    sum_val = 0;
                    for jj = 1:6
                        temp = Q_1(i_rw + 3, jj) * U_1(jj) * (C_s1 / (zeta_1 - LAMBDA_1(jj)) + ...
                               C_s2 / (-zeta_1 - LAMBDA_1(jj)));
                        sum_val = sum_val + temp;
                    end
                    BCC(i_rw) = -sum_val;
                end
                % if i_p == 1 && i_psi == 1 && i_fr == 1
                %     fprintf('MATLAB BCC(4) summation terms at Z_p_psi_omega[1,1,1] (freq %.2f Hz):\n', ff(i_fr));
                %     fprintf('  Q1(1:3, :):\n');
                %     for j = 1:6
                %         fprintf('    Q1(1:3,%d): real: [%.6e, %.6e, %.6e], imag: [%.6e, %.6e, %.6e]\n', ...
                %                 j, real(Q_1(1:3,j))', imag(Q_1(1:3,j))');
                %     end
                %     fprintf('  U1(1:6):\n');
                %     for j = 1:6
                %         fprintf('    U1(%d): real: %.6e, imag: %.6e, abs: %.6e\n', ...
                %                 j, real(U_1(j)), imag(U_1(j)), abs(U_1(j)));
                %     end
                % end
                for i_rw = 4:6
                    sum1 = 0; sum2 = 0;
                    for jj = 1:6
                        temp1 = Q_1(i_rw-3,jj)*U_1(jj)*(C_s1*exp(zeta_1L_1)/(zeta_1-LAMBDA_1(jj)) + C_s2*exp(-zeta_1L_1)/(-zeta_1-LAMBDA_1(jj)));
                        temp2 = Q_2(i_rw-3,jj)*U_2(jj)*(theta_bs/(-zeta_2-LAMBDA_2(jj)));
                        sum1 = sum1 + temp1;
                        sum2 = sum2 + temp2;
                        % if i_p == 1 && i_psi == 1 && i_fr == 1 && i_rw == 4
                        %     fprintf('  BCC(4) summand jj=%d:\n', jj);
                        %     fprintf('    temp1: real: %.6e, imag: %.6e, abs: %.6e\n', ...
                        %             real(temp1), imag(temp1), abs(temp1));
                        %     fprintf('    temp2: real: %.6e, imag: %.6e, abs: %.6e\n', ...
                        %             real(temp2), imag(temp2), abs(temp2));
                        % end
                    end
                    BCC(i_rw) = -sum1 + sum2;
                    % if i_p == 1 && i_psi == 1 && i_fr == 1 && i_rw == 4
                    %     fprintf('  BCC(4) sum1: real: %.6e, imag: %.6e, abs: %.6e\n', ...
                    %             real(sum1), imag(sum1), abs(sum1));
                    %     fprintf('  BCC(4) sum2: real: %.6e, imag: %.6e, abs: %.6e\n', ...
                    %             real(sum2), imag(sum2), abs(sum2));
                    %     fprintf('  BCC(4): real: %.6e, imag: %.6e, abs: %.6e\n', ...
                    %             real(BCC(i_rw)), imag(BCC(i_rw)), abs(BCC(i_rw)));
                    % end
                end
                for i_rw = 7:9
                    sum1 = 0; sum2 = 0;
                    for jj = 1:6
                        temp1 = Q_1(i_rw - 3, jj) * U_1(jj) * (C_s1 * exp(zeta_1L_1) / ...
                                (zeta_1 - LAMBDA_1(jj)) + C_s2 * exp(-zeta_1L_1) / ...
                                (-zeta_1 - LAMBDA_1(jj)));
                        temp2 = Q_2(i_rw - 3, jj) * U_2(jj) * (theta_bs / (-zeta_2 - LAMBDA_2(jj)));
                        sum1 = sum1 + temp1;
                        sum2 = sum2 + temp2;
                    end
                    BCC(i_rw) = -sum1 + (params.mat2.C11_0_2 / params.mat1.C11_1) * sum2;
                end
                % if i_p == 1 && i_psi == 1 && i_fr == 1
                %     fprintf('MATLAB BCM and BCC at Z_p_psi_omega[1,1,1] (freq %.2f Hz):\n', ff(i_fr));
                %     fprintf('  BCM selected elements:\n');
                %     fprintf('    BCM(1,1): real: %.6e, imag: %.6e, abs: %.6e\n', ...
                %             real(BCM(1,1)), imag(BCM(1,1)), abs(BCM(1,1)));
                %     fprintf('    BCM(4,7): real: %.6e, imag: %.6e, abs: %.6e\n', ...
                %             real(BCM(4,7)), imag(BCM(4,7)), abs(BCM(4,7)));
                %     fprintf('  BCC selected elements:\n');
                %     fprintf('    BCC(1): real: %.6e, imag: %.6e, abs: %.6e\n', ...
                %             real(BCC(1)), imag(BCC(1)), abs(BCC(1)));
                %     fprintf('    BCC(4): real: %.6e, imag: %.6e, abs: %.6e\n', ...
                %             real(BCC(4)), imag(BCC(4)), abs(BCC(4)));
                %     fprintf('  Thermal terms:\n');
                %     fprintf('    C_s1: real: %.6e, imag: %.6e, abs: %.6e\n', ...
                %             real(C_s1), imag(C_s1), abs(C_s1));
                %     fprintf('    C_s2: real: %.6e, imag: %.6e, abs: %.6e\n', ...
                %             real(C_s2), imag(C_s2), abs(C_s2));
                %     fprintf('    theta_s: real: %.6e, imag: %.6e, abs: %.6e\n', ...
                %             real(theta_s), imag(theta_s), abs(theta_s));
                %     fprintf('    theta_bs: real: %.6e, imag: %.6e, abs: %.6e\n', ...
                %             real(theta_bs), imag(theta_bs), abs(theta_bs));
                % end
                J = BCM \ BCC;
                if i_p == 1 && i_psi == 1 && i_fr == 1
                    fprintf('MATLAB J at Z_p_psi_omega[1,1,1] (freq %.2f Hz):\n', ff(i_fr));
                    for m = 1:9
                        fprintf('  J(%d): real: %.6e, imag: %.6e, abs: %.6e\n', ...
                                m, real(J(m)), imag(J(m)), abs(J(m)));
                    end
                end
                w_s_H = Q_1(3, 1) * J(1) + Q_1(3, 2) * J(2) + Q_1(3, 3) * J(3) + ...
                        Q_1(3, 4) * J(4) + Q_1(3, 5) * J(5) + Q_1(3, 6) * J(6);
                sssum = 0;
                for jj = 1:6
                    temp = Q_1(3, jj) * U_1(jj) * (C_s1 / (zeta_1 - LAMBDA_1(jj)) + ...
                           C_s2 / (-zeta_1 - LAMBDA_1(jj)));
                    sssum = sssum + temp;
                end
                w_s_P = sssum;
                Z_p_psi_omega(i_p, i_psi, i_fr) = -(w_s_H + w_s_P);
                % if i_p == 1 && i_psi == 1 && i_fr == 1
                %     fprintf('MATLAB at Z_p_psi_omega[1,1,1] (freq %.2f Hz):\n', ff(i_fr));
                %     fprintf('  w_s_H: real: %.6e, imag: %.6e, abs: %.6e\n', ...
                %             real(w_s_H), imag(w_s_H), abs(w_s_H));
                %     fprintf('  w_s_P: real: %.6e, imag: %.6e, abs: %.6e\n', ...
                %             real(w_s_P), imag(w_s_P), abs(w_s_P));
                %     fprintf('  Z: real: %.6e, imag: %.6e, abs: %.6e\n', ...
                %             real(Z_p_psi_omega(i_p,i_psi,i_fr)), ...
                %             imag(Z_p_psi_omega(i_p,i_psi,i_fr)), ...
                %             abs(Z_p_psi_omega(i_p,i_psi,i_fr)));
                % end
            end
        end
    end
end

function PBD_angle = calculate_probe_beam_deflection(Z_p_psi_omega, params, constants)
    % Calculate probe beam deflection angle
    ff = params.ff;
    w_rms = params.beam.w_rms;
    r_0 = params.beam.r_0;
    phi = params.beam.phi;
    n_p = constants.n_p;
    n_psi = constants.n_psi;
    up_p = 8 / w_rms;
    d_p = up_p / n_p;
    up_psi = pi / 2;
    d_psi = up_psi / n_psi;
    ppsi = 0:d_psi:up_psi;
    pp = d_p:d_p:up_p;

    PBD_angle = ones(length(ff), 1);
    for i_fr = 1:length(ff)
        Ip2 = zeros(n_p, 1);
        for i_p = 1:n_p
            p = pp(i_p);
            pr0 = p * r_0;
            Zg = zeros(n_psi, 1);
            for i_psi = 1:n_psi
                psi = ppsi(i_psi);
                g_psi_phi = -cos(psi - phi) * sin(pr0 * cos(psi - phi)) - ...
                            cos(psi + phi) * sin(pr0 * cos(psi + phi));
                Zg(i_psi) = Z_p_psi_omega(i_p, i_psi, i_fr) * g_psi_phi;
            end
            I_p_r0_phi = 1 / pi * simpson_inte(Zg, d_psi);
            Ip2(i_p) = I_p_r0_phi * exp(-w_rms^2 * p^2 / 8) * p^2;
        end
        PBD_angle(i_fr, 1) = 1 / pi * constants.C_probe * simpson_inte(Ip2, d_p);
    end
end

function signals = calculate_lockin_signals(PBD_angle, V_sum, constants)
    % Calculate lock-in amplifier signals
    PBD_signal = PBD_angle / sqrt(2) * 0.5 * 37.0 * V_sum;
    signals.in_phase = abs(real(PBD_signal));
    signals.out_of_phase = -imag(PBD_signal);
    signals.ratio = -signals.in_phase ./ signals.out_of_phase;
end

function analysis = analyze_signals(signals, ff)
    % Rough analysis of signals
    p = polyfit(log(ff), signals.out_of_phase, 2);
    analysis.fmax = exp(-p(2) / (2 * p(1)));
    p = polyfit(log(ff), log(signals.ratio), 1);
    analysis.ratio_at_fmax = exp(polyval(p, log(analysis.fmax)));
    fprintf('Frequency of maximum of out-of-phase: %.2f Hz\n', analysis.fmax);
    fprintf('Ratio at that frequency: %.4f\n', analysis.ratio_at_fmax);
end

function plot_results(ff, signals, exp_data, analysis)
    % Plot model and experimental results
    figure(104);
    subplot(1, 2, 1);
    semilogx(ff, signals.in_phase, 'ko-', 'linewidth', 1.5, 'DisplayName', 'Model In-phase'); hold on;
    semilogx(ff, signals.out_of_phase, 'kx--', 'linewidth', 1.5, 'DisplayName', 'Model Out-of-phase'); hold on;
    semilogx(exp_data.Fexp, exp_data.Vin_exp, 'ro-', 'linewidth', 1.5, 'DisplayName', 'Exp In-phase'); hold on;
    semilogx(exp_data.Fexp, exp_data.Vout_exp, 'rx--', 'linewidth', 1.5, 'DisplayName', 'Exp Out-of-phase'); hold on;
    box on; axis tight;
    set(gca, 'linewidth', 1.5, 'fontsize', 16, 'fontname', 'Times New Roman');
    xlabel('f (Hz)');
    ylabel('In, Out-of-phase (V)');
    legend('show', 'Location', 'best');

    subplot(1, 2, 2);
    loglog(ff, signals.ratio, 'ko-', 'linewidth', 1.5, 'DisplayName', 'Model Ratio'); hold on;
    loglog(exp_data.Fexp, exp_data.ratio, 'ro-', 'linewidth', 1.5, 'DisplayName', 'Exp Ratio'); hold on;
    box on; axis tight;
    set(gca, 'linewidth', 1.5, 'fontsize', 16, 'fontname', 'Times New Roman');
    xlabel('f (Hz)');
    ylabel('Ratio');
    legend('show', 'Location', 'best');
end

function I = simpson_inte(array, pace)
    % Simpson's rule integration
    steps = length(array);
    edge_sum = sum(array(3:2:steps-2));
    mid_sum = sum(array(2:2:steps-1));
    I = (1/6) * (2 * pace) * (array(1) + 2 * edge_sum + 4 * mid_sum + array(steps));
end

% Run the main function
thermoelastic_model();