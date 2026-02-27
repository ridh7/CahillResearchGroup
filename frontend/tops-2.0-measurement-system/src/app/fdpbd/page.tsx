'use client';

import { useState } from 'react';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { API_BASE } from '../../lib/api';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

type IsotropicPlotData = {
  freq_fit: number[];
  v_corr_in_fit: number[];
  v_corr_out_fit: number[];
  v_corr_ratio_fit: number[];
  delta_in: number[];
  delta_out: number[];
  delta_ratio: number[];
};

type AnisotropicPlotData = {
  model_freqs: number[];
  in_model: number[];
  out_model: number[];
  ratio_model: number[];
  exp_freqs: number[];
  in_exp: number[];
  out_exp: number[];
  ratio_exp: number[];
};

type TransverseIsotropicPlotData = {
  model_freqs: number[];
  in_model: number[];
  out_model: number[];
  ratio_model: number[];
  exp_freqs: number[];
  in_exp: number[];
  out_exp: number[];
  ratio_exp: number[];
};

type FDPBDResult = {
  lambda_measure: number;
  alpha_t_fitted: number;
  t_ss_heat: number;
  plot_data: IsotropicPlotData;
};

type AnisotropicFDPBDResult = {
  f_peak: number | null;
  ratio_at_peak: number | null;
  lambda_measure: number | null;
  alpha_t_fitted: number | null;
  t_ss_heat: number | null;
  plot_data: AnisotropicPlotData;
};

type TransverseIsotropicResult = {
  plot_data: TransverseIsotropicPlotData;
};

type FDPBDParams = {
  f_rolloff: string;
  delay_1: string;
  delay_2: string;
  lambda_down: string[];
  eta_down: string[];
  c_down: string[];
  h_down: string[];
  niu: string;
  alpha_t: string;
  lambda_up: string;
  eta_up: string;
  c_up: string;
  h_up: string;
  w_rms: string;
  x_offset: string;
  incident_pump: string;
  incident_probe: string;
  n_al: string;
  k_al: string;
  lens_transmittance: string;
  detector_factor: string;
  phi: string;
  rho: string;
  alphaT: string;
  C11_0: string;
  C12_0: string;
  C44_0: string;
  lambda_down_x_sample: string;
  lambda_down_y_sample: string;
  lambda_down_z_sample: string;
  rho_sample: string;
  C11_0_sample: string;
  C12_0_sample: string;
  C13_0_sample: string;
  C33_0_sample: string;
  C44_0_sample: string;
  alphaT_perp: string;
  alphaT_para: string;
  // Transverse anisotropy specific (unique fields not shared with other modes)
  v_sum_fixed: string;
  c_probe: string;
  g_int: string;
};

export default function FDPBDPage() {
  const [params, setParams] = useState<FDPBDParams>({
    f_rolloff: '95000',
    delay_1: '0.0000089',
    delay_2: '-1.3e-11',
    lambda_down: ['149.0', '0.1', '9.7'],
    eta_down: ['1.0', '1.0', '1.0'],
    c_down: ['2.44', '0.1', '2.73'],
    h_down: ['0.07', '0.001', '1'],
    niu: '0.26',
    alpha_t: '0.00001885',
    lambda_up: '0.028',
    eta_up: '1.0',
    c_up: '1192.0',
    h_up: '0.001',
    w_rms: '11.20',
    x_offset: '12.60',
    incident_pump: '1.06',
    incident_probe: '0.85',
    n_al: '2.9',
    k_al: '8.2',
    lens_transmittance: '0.93',
    detector_factor: '74.0',
    phi: '0',
    rho: '2.70',
    alphaT: '23.1e-6',
    C11_0: '107.4',
    C12_0: '60.5',
    C44_0: '28.3',
    lambda_down_x_sample: '0.3',
    lambda_down_y_sample: '0.5',
    lambda_down_z_sample: '0.3',
    rho_sample: '1.38',
    C11_0_sample: '12.11',
    C12_0_sample: '5.06',
    C13_0_sample: '5.68',
    C33_0_sample: '7.06',
    C44_0_sample: '1.20',
    alphaT_perp: '70e-6',
    alphaT_para: '60e-6',
    // Transverse anisotropy defaults (from main_3.py)
    v_sum_fixed: '0.18',
    c_probe: '0.65',
    g_int: '100e6',
  });
  const fieldUnits: Record<string, string> = {
    f_rolloff: 'Hz',
    delay_1: 's',
    delay_2: 's',
    lambda_down: 'W/m-K',
    eta_down: '',
    c_down: 'J/cm\u00B3-K',
    h_down: '\u00B5m',
    niu: '',
    alpha_t: '1/K',
    lambda_up: 'W/m-K',
    eta_up: '',
    c_up: 'J/m\u00B3-K',
    h_up: 'm',
    w_rms: '\u00B5m',
    x_offset: '\u00B5m',
    incident_pump: 'mW',
    incident_probe: 'mW',
    n_al: '',
    k_al: '',
    lens_transmittance: '',
    detector_factor: 'V/rad',
    phi: 'degrees',
    rho: 'g/cm\u00B3',
    alphaT: '1/K',
    C11_0: 'GPa',
    C12_0: 'GPa',
    C44_0: 'GPa',
    lambda_down_x_sample: 'W/m-K',
    lambda_down_y_sample: 'W/m-K',
    lambda_down_z_sample: 'W/m-K',
    rho_sample: 'g/cm\u00B3',
    C11_0_sample: 'GPa',
    C12_0_sample: 'GPa',
    C13_0_sample: 'GPa',
    C33_0_sample: 'GPa',
    C44_0_sample: 'GPa',
    alphaT_perp: '1/K',
    alphaT_para: '1/K',
    v_sum_fixed: 'V',
    c_probe: '',
    g_int: 'W/m\u00B2-K',
  };
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<
    FDPBDResult | AnisotropicFDPBDResult | TransverseIsotropicResult | null
  >(null);
  const [status, setStatus] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [lensOption, setLensOption] = useState<'5x' | '10x' | '20x' | 'custom'>('5x');
  const [transducerOption, setTransducerOption] = useState<'Al' | 'custom'>('Al');
  const [mediumOption, setMediumOption] = useState<'air' | 'custom'>('air');
  const [isotropyOption, setIsotropyOption] = useState<
    'isotropy' | 'anisotropy' | 'transverse_anisotropy'
  >('isotropy');
  const [laserOption, setLaserOption] = useState<'TOPS 1' | 'TOPS 2' | 'custom'>('TOPS 1');

  const isValidDecimal = (value: string | string[]) => {
    if (Array.isArray(value)) {
      return value.every((v) => v !== '' && !isNaN(parseFloat(v)));
    }
    return value !== '' && !isNaN(parseFloat(value));
  };

  const isFormValid = () => {
    if (isotropyOption === 'transverse_anisotropy') {
      const fields = [
        params.f_rolloff,
        params.delay_1,
        params.delay_2,
        params.incident_pump,
        params.v_sum_fixed,
        params.w_rms,
        params.x_offset,
        params.lens_transmittance,
        params.detector_factor,
        params.c_probe,
        params.n_al,
        params.k_al,
        params.g_int,
        // Transducer (Layer 1)
        params.lambda_down[0],
        params.c_down[0],
        params.h_down[0],
        params.rho,
        params.alphaT,
        params.C11_0,
        params.C12_0,
        params.C44_0,
        // Sample (Layer 2)
        params.lambda_down_x_sample,
        params.lambda_down_z_sample,
        params.c_down[2],
        params.rho_sample,
        params.alphaT_perp,
        params.alphaT_para,
        params.C11_0_sample,
        params.C12_0_sample,
        params.C13_0_sample,
        params.C33_0_sample,
        params.C44_0_sample,
        // Medium (Layer 3)
        params.lambda_up,
        params.c_up,
      ];
      return fields.every((field) => isValidDecimal(field)) && file !== null;
    }
    const fields = [
      params.f_rolloff,
      params.delay_1,
      params.delay_2,
      params.lambda_down[0],
      params.lambda_down[1],
      params.lambda_down[2],
      ...(isotropyOption === 'isotropy'
        ? [params.eta_down[0], params.eta_down[1], params.eta_down[2]]
        : []),
      params.c_down[0],
      params.c_down[1],
      params.c_down[2],
      params.h_down[0],
      params.h_down[1],
      params.h_down[2],
      ...(isotropyOption === 'isotropy' ? [params.niu, params.alpha_t] : []),
      params.lambda_up,
      ...(isotropyOption === 'isotropy' ? [params.eta_up, params.h_up] : []),
      params.c_up,
      params.w_rms,
      params.x_offset,
      params.incident_pump,
      params.incident_probe,
      params.n_al,
      params.k_al,
      params.lens_transmittance,
      params.detector_factor,
      ...(isotropyOption === 'anisotropy'
        ? [
            params.phi,
            params.rho,
            params.alphaT,
            params.C11_0,
            params.C12_0,
            params.C44_0,
            params.lambda_down_x_sample,
            params.lambda_down_y_sample,
            params.lambda_down_z_sample,
            params.rho_sample,
            params.C11_0_sample,
            params.C12_0_sample,
            params.C13_0_sample,
            params.C33_0_sample,
            params.C44_0_sample,
            params.alphaT_perp,
            params.alphaT_para,
          ]
        : []),
    ];
    return fields.every((field) => isValidDecimal(field)) && file !== null;
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement>,
    field: keyof FDPBDParams,
    index?: number
  ) => {
    const value = e.target.value;
    setParams((prev) => {
      if (index !== undefined && ['lambda_down', 'c_down', 'h_down'].includes(field)) {
        const updatedArray = [...prev[field]];
        updatedArray[index] = value;
        return { ...prev, [field]: updatedArray };
      }
      return { ...prev, [field]: value };
    });

    if (['w_rms', 'x_offset', 'lens_transmittance', 'detector_factor', 'phi'].includes(field)) {
      const lensValues = {
        '5x': {
          w_rms: '11.20',
          x_offset: '12.60',
          lens_transmittance: '0.93',
          detector_factor: '74.0',
          phi: '0',
        },
        '10x': {
          w_rms: '5.60',
          x_offset: '6.30',
          lens_transmittance: '0.85',
          detector_factor: '37.0',
          phi: '0',
        },
        '20x': {
          w_rms: '2.825',
          x_offset: '3.15',
          lens_transmittance: '0.80',
          detector_factor: '18.5',
          phi: '0',
        },
      };
      const updatedParams = { ...params, [field]: value };
      if (
        !Object.values(lensValues).some(
          (vals) =>
            vals.w_rms === updatedParams.w_rms &&
            vals.x_offset === updatedParams.x_offset &&
            vals.lens_transmittance === updatedParams.lens_transmittance &&
            vals.detector_factor === updatedParams.detector_factor &&
            vals.phi === updatedParams.phi
        )
      ) {
        setLensOption('custom');
      }
    }
    if (
      (['lambda_down', 'c_down', 'h_down'].includes(field) && index === 0) ||
      ['n_al', 'k_al', 'rho', 'alphaT', 'C11_0', 'C12_0', 'C44_0'].includes(field)
    ) {
      const alValues = {
        lambda_down_0: '149.0',
        c_down_0: '2.44',
        h_down_0: '0.07',
        n_al: '2.9',
        k_al: '8.2',
        rho: '2.70',
        alphaT: '23.1e-6',
        C11_0: '107.4',
        C12_0: '60.5',
        C44_0: '28.3',
      };
      const updatedParams =
        index !== undefined
          ? {
              ...params,
              [field]: [...params[field].slice(0, index), value, ...params[field].slice(index + 1)],
            }
          : { ...params, [field]: value };
      if (
        !(
          updatedParams.lambda_down[0] === alValues.lambda_down_0 &&
          updatedParams.c_down[0] === alValues.c_down_0 &&
          updatedParams.h_down[0] === alValues.h_down_0 &&
          updatedParams.n_al === alValues.n_al &&
          updatedParams.k_al === alValues.k_al &&
          (isotropyOption === 'isotropy' ||
            (updatedParams.rho === alValues.rho &&
              updatedParams.alphaT === alValues.alphaT &&
              updatedParams.C11_0 === alValues.C11_0 &&
              updatedParams.C12_0 === alValues.C12_0 &&
              updatedParams.C44_0 === alValues.C44_0))
        )
      ) {
        setTransducerOption('custom');
      }
    }
    if (['lambda_up', 'eta_up', 'c_up', 'h_up'].includes(field)) {
      const airValues = {
        lambda_up: '0.028',
        eta_up: '1.0',
        c_up: '1192.0',
        h_up: '0.001',
      };
      const updatedParams = { ...params, [field]: value };
      if (
        !(
          updatedParams.lambda_up === airValues.lambda_up &&
          (isotropyOption !== 'isotropy' || updatedParams.eta_up === airValues.eta_up) &&
          updatedParams.c_up === airValues.c_up &&
          (isotropyOption !== 'isotropy' || updatedParams.h_up === airValues.h_up)
        )
      ) {
        setMediumOption('custom');
      }
    }
    if (field === 'eta_down' && index !== undefined) {
      const isotropyValue = ['1.0', '1.0', '1.0'];
      const updatedArray = [...params.eta_down];
      updatedArray[index] = value;
      setParams((prev) => ({ ...prev, eta_down: updatedArray }));
      if (updatedArray.join(',') !== isotropyValue.join(',')) {
        setIsotropyOption('anisotropy');
      }
    }
    if (['f_rolloff', 'delay_1', 'delay_2', 'incident_pump', 'incident_probe'].includes(field)) {
      const laserValues = {
        'TOPS 1': {
          f_rolloff: '95000',
          delay_1: '0.0000089',
          delay_2: '-1.3e-11',
          incident_pump: '1.06',
          incident_probe: '0.85',
        },
        'TOPS 2': {
          f_rolloff: '95000',
          delay_1: '0.0000089',
          delay_2: '-1.3e-11',
          incident_pump: '1.06',
          incident_probe: '0.85',
        },
      };
      const updatedParams = { ...params, [field]: value };
      if (
        !Object.values(laserValues).some(
          (vals) =>
            vals.f_rolloff === updatedParams.f_rolloff &&
            vals.delay_1 === updatedParams.delay_1 &&
            vals.delay_2 === updatedParams.delay_2 &&
            vals.incident_pump === updatedParams.incident_pump &&
            vals.incident_probe === updatedParams.incident_probe
        )
      ) {
        setLaserOption('custom');
      }
    }
  };

  const handleLensOptionChange = (option: '5x' | '10x' | '20x' | 'custom') => {
    setLensOption(option);
    if (option !== 'custom') {
      const values = {
        '5x': {
          w_rms: '11.20',
          x_offset: '12.60',
          lens_transmittance: '0.93',
          detector_factor: '74.0',
          phi: '0',
        },
        '10x': {
          w_rms: '5.60',
          x_offset: '6.30',
          lens_transmittance: '0.85',
          detector_factor: '37.0',
          phi: '0',
        },
        '20x': {
          w_rms: '2.825',
          x_offset: '3.15',
          lens_transmittance: '0.80',
          detector_factor: '18.5',
          phi: '0',
        },
      };
      setParams((prev) => ({
        ...prev,
        w_rms: values[option].w_rms,
        x_offset: values[option].x_offset,
        lens_transmittance: values[option].lens_transmittance,
        detector_factor: values[option].detector_factor,
        phi: values[option].phi,
      }));
    }
  };

  const handleTransducerOptionChange = (option: 'Al' | 'custom') => {
    setTransducerOption(option);
    if (option === 'Al') {
      setParams((prev) => ({
        ...prev,
        lambda_down: ['149.0', prev.lambda_down[1], prev.lambda_down[2]],
        c_down: ['2.44', prev.c_down[1], prev.c_down[2]],
        h_down: ['0.07', prev.h_down[1], prev.h_down[2]],
        n_al: '2.9',
        k_al: '8.2',
        rho: isotropyOption !== 'isotropy' ? '2.70' : prev.rho,
        alphaT: isotropyOption !== 'isotropy' ? '23.1e-6' : prev.alphaT,
        C11_0: isotropyOption !== 'isotropy' ? '107.4' : prev.C11_0,
        C12_0: isotropyOption !== 'isotropy' ? '60.5' : prev.C12_0,
        C44_0: isotropyOption !== 'isotropy' ? '28.3' : prev.C44_0,
      }));
    }
  };

  const handleMediumOptionChange = (option: 'air' | 'custom') => {
    setMediumOption(option);
    if (option === 'air') {
      setParams((prev) => ({
        ...prev,
        lambda_up: '0.028',
        eta_up: isotropyOption === 'isotropy' ? '1.0' : prev.eta_up,
        c_up: '1192.0',
        h_up: isotropyOption === 'isotropy' ? '0.001' : prev.h_up,
      }));
    }
  };

  const handleIsotropyOptionChange = (
    option: 'isotropy' | 'anisotropy' | 'transverse_anisotropy'
  ) => {
    setIsotropyOption(option);
    setResult(null);
    if (option === 'isotropy') {
      setParams((prev) => ({
        ...prev,
        eta_down: ['1.0', '1.0', '1.0'],
      }));
    }
    if (option === 'transverse_anisotropy') {
      // Set transverse-specific defaults and appropriate shared field defaults
      setParams((prev) => ({
        ...prev,
        // Transverse-only fields
        v_sum_fixed: prev.v_sum_fixed || '0.18',
        c_probe: prev.c_probe || '0.65',
        g_int: prev.g_int || '100e6',
        // Set transducer defaults for transverse mode
        rho: '2.70',
        alphaT: '23.1e-6',
        C11_0: '107.4',
        C12_0: '60.5',
        C44_0: '28.3',
        // Set sample layer defaults for transverse mode
        lambda_down_x_sample: '0.64',
        lambda_down_z_sample: '0.21',
        c_down: [prev.c_down[0], prev.c_down[1], '1.56'],
        rho_sample: '1.43',
        C11_0_sample: '8.9',
        C12_0_sample: '5.4',
        C13_0_sample: '5.4',
        C33_0_sample: '5.6',
        C44_0_sample: '2.1',
        alphaT_perp: '28e-6',
        alphaT_para: '120e-6',
      }));
      setTransducerOption('Al');
      setMediumOption('air');
    }
  };

  const handleLaserOptionChange = (option: 'TOPS 1' | 'TOPS 2' | 'custom') => {
    setLaserOption(option);
    if (option !== 'custom') {
      const values = {
        'TOPS 1': {
          f_rolloff: '95000',
          delay_1: '0.0000089',
          delay_2: '-1.3e-11',
          incident_pump: '1.06',
          incident_probe: '0.85',
        },
        'TOPS 2': {
          f_rolloff: '95000',
          delay_1: '0.0000089',
          delay_2: '-1.3e-11',
          incident_pump: '1.06',
          incident_probe: '0.85',
        },
      };
      setParams((prev) => ({
        ...prev,
        f_rolloff: values[option].f_rolloff,
        delay_1: values[option].delay_1,
        delay_2: values[option].delay_2,
        incident_pump: values[option].incident_pump,
        incident_probe: values[option].incident_probe,
      }));
    }
  };

  const handleClear = () => {
    setParams({
      f_rolloff: '',
      delay_1: '',
      delay_2: '',
      lambda_down: ['', '', ''],
      eta_down: ['', '', ''],
      c_down: ['', '', ''],
      h_down: ['', '', ''],
      niu: '',
      alpha_t: '',
      lambda_up: '',
      eta_up: '',
      c_up: '',
      h_up: '',
      w_rms: '',
      x_offset: '',
      incident_pump: '',
      incident_probe: '',
      n_al: '',
      k_al: '',
      lens_transmittance: '',
      detector_factor: '',
      phi: '',
      rho: '',
      alphaT: '',
      C11_0: '',
      C12_0: '',
      C44_0: '',
      lambda_down_x_sample: '',
      lambda_down_y_sample: '',
      lambda_down_z_sample: '',
      rho_sample: '',
      C11_0_sample: '',
      C12_0_sample: '',
      C13_0_sample: '',
      C33_0_sample: '',
      C44_0_sample: '',
      alphaT_perp: '',
      alphaT_para: '',
      v_sum_fixed: '',
      c_probe: '',
      g_int: '',
    });
    setFile(null);
    setLensOption('custom');
    setTransducerOption('custom');
    setMediumOption('custom');
    setIsotropyOption('anisotropy');
    setLaserOption('custom');
    setStatus('');
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && selectedFile.type === 'text/plain') {
      setFile(selectedFile);
      setStatus('');
    } else {
      setFile(null);
      setStatus('Please upload a .txt file');
    }
  };

  const handleSubmit = async () => {
    if (!file) {
      setStatus('Please upload a data file');
      return;
    }
    setIsProcessing(true);
    setStatus('Processing...');

    const formData = new FormData();
    formData.append('file', file);

    if (isotropyOption === 'transverse_anisotropy') {
      // Transverse anisotropy mode: map shared fields to backend param names with unit conversions
      const transverseParams = {
        f_rolloff: parseFloat(params.f_rolloff),
        delay_1: parseFloat(params.delay_1),
        delay_2: parseFloat(params.delay_2),
        incident_pump: parseFloat(params.incident_pump) * 1e-3, // mW -> W
        v_sum_fixed: parseFloat(params.v_sum_fixed),
        w_rms: parseFloat(params.w_rms) * 1e-6, // µm -> m
        r_0: parseFloat(params.x_offset) * 1e-6, // µm -> m (x_offset -> r_0)
        lens_transmittance: parseFloat(params.lens_transmittance),
        detector_gain: parseFloat(params.detector_factor), // detector_factor -> detector_gain
        c_probe: parseFloat(params.c_probe),
        n_al: parseFloat(params.n_al),
        k_al: parseFloat(params.k_al),
        g_int: parseFloat(params.g_int),
        // Layer 1 (Transducer / Al film) from shared fields
        layer1_thickness: parseFloat(params.h_down[0]) * 1e-6, // µm -> m
        layer1_sigma: parseFloat(params.lambda_down[0]), // W/m-K
        layer1_capac: parseFloat(params.c_down[0]) * 1e6, // J/cm³-K -> J/m³-K
        layer1_rho: parseFloat(params.rho) * 1e3, // g/cm³ -> kg/m³
        layer1_alphaT: parseFloat(params.alphaT), // 1/K
        layer1_C11_0: parseFloat(params.C11_0) * 1e9, // GPa -> Pa
        layer1_C12_0: parseFloat(params.C12_0) * 1e9, // GPa -> Pa
        layer1_C44_0: parseFloat(params.C44_0) * 1e9, // GPa -> Pa
        // Layer 2 (Sample / bulk) from shared fields
        layer2_sigma_r: parseFloat(params.lambda_down_x_sample), // W/m-K (in-plane)
        layer2_sigma_z: parseFloat(params.lambda_down_z_sample), // W/m-K (through-plane)
        layer2_capac: parseFloat(params.c_down[2]) * 1e6, // J/cm³-K -> J/m³-K
        layer2_rho: parseFloat(params.rho_sample) * 1e3, // g/cm³ -> kg/m³
        layer2_alphaT_perp: parseFloat(params.alphaT_perp), // 1/K
        layer2_alphaT_para: parseFloat(params.alphaT_para), // 1/K
        layer2_C11_0: parseFloat(params.C11_0_sample) * 1e9, // GPa -> Pa
        layer2_C12_0: parseFloat(params.C12_0_sample) * 1e9, // GPa -> Pa
        layer2_C13_0: parseFloat(params.C13_0_sample) * 1e9, // GPa -> Pa
        layer2_C33_0: parseFloat(params.C33_0_sample) * 1e9, // GPa -> Pa
        layer2_C44_0: parseFloat(params.C44_0_sample) * 1e9, // GPa -> Pa
        // Layer 3 (Air / medium) from shared fields
        layer3_sigma: parseFloat(params.lambda_up), // W/m-K
        layer3_capac: parseFloat(params.c_up), // J/m³-K
      };
      formData.append('params', JSON.stringify(transverseParams));

      try {
        const response = await fetch(`${API_BASE}/fdpbd/analyze_transverse`, {
          method: 'POST',
          body: formData,
        });
        const data = await response.json();
        if (response.ok) {
          setResult(data);
          setStatus('Analysis completed');
        } else {
          setStatus(`Error: ${data.detail || 'Unknown error'}`);
        }
      } catch (error) {
        console.error('Error:', error);
        setStatus('Error occurred during analysis');
      } finally {
        setIsProcessing(false);
      }
      return;
    }

    const modifiedParams = {
      ...params,
      w_rms: (parseFloat(params.w_rms) * 1e-6).toString(),
      x_offset: (parseFloat(params.x_offset) * 1e-6).toString(),
      incident_probe: (parseFloat(params.incident_probe) * 1e-3).toString(),
      incident_pump: (parseFloat(params.incident_pump) * 1e-3).toString(),
      c_down: params.c_down.map((c_down_i) => (parseFloat(c_down_i) * 1e6).toString()),
      h_down: params.h_down.map((h_down_i) => (parseFloat(h_down_i) * 1e-6).toString()),
      rho: (parseFloat(params.rho) * 1e3).toString(),
      rho_sample: (parseFloat(params.rho_sample) * 1e3).toString(),
      C11_0: (parseFloat(params.C11_0) * 1e9).toString(),
      C12_0: (parseFloat(params.C12_0) * 1e9).toString(),
      C44_0: (parseFloat(params.C44_0) * 1e9).toString(),
      C11_0_sample: (parseFloat(params.C11_0_sample) * 1e9).toString(),
      C12_0_sample: (parseFloat(params.C12_0_sample) * 1e9).toString(),
      C13_0_sample: (parseFloat(params.C13_0_sample) * 1e9).toString(),
      C33_0_sample: (parseFloat(params.C33_0_sample) * 1e9).toString(),
      C44_0_sample: (parseFloat(params.C44_0_sample) * 1e9).toString(),
    };

    const visibleParams = {
      ...modifiedParams,
      eta_down: isotropyOption === 'isotropy' ? modifiedParams.eta_down.join(',') : undefined,
      ...(isotropyOption === 'anisotropy'
        ? {
            eta_up: undefined,
            h_up: undefined,
            lambda_down: [modifiedParams.lambda_down[0]],
            h_down: [modifiedParams.h_down[0]],
            niu: undefined,
            alpha_t: undefined,
          }
        : {
            phi: undefined,
            rho: undefined,
            alphaT: undefined,
            C11_0: undefined,
            C12_0: undefined,
            C44_0: undefined,
            lambda_down_x_sample: undefined,
            lambda_down_y_sample: undefined,
            lambda_down_z_sample: undefined,
            rho_sample: undefined,
            C11_0_sample: undefined,
            C12_0_sample: undefined,
            C13_0_sample: undefined,
            C33_0_sample: undefined,
            C44_0_sample: undefined,
            alphaT_perp: undefined,
            alphaT_para: undefined,
          }),
    };
    formData.append('params', JSON.stringify(visibleParams));

    try {
      const endpoint =
        isotropyOption === 'isotropy'
          ? `${API_BASE}/fdpbd/analyze`
          : `${API_BASE}/fdpbd/analyze_anisotropy`;
      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (response.ok) {
        setResult(data);
        setStatus('Analysis completed');
      } else {
        setStatus(`Error: ${data.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error:', error);
      setStatus('Error occurred during analysis');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-gray-900">
      {/* Header */}
      <header className="flex items-center justify-between bg-gray-800 p-4">
        <h1 className="text-xl font-semibold text-white">Analysis</h1>
        <Link href="/" className="text-white hover:text-teal-400">
          Back to Dashboard
        </Link>
      </header>

      {/* Main Layout */}
      <div className="flex flex-1 space-x-4 p-4">
        {/* Left Panel: Input Form */}
        <div className="flex w-1/3 flex-col space-y-4">
          <div className="rounded-lg bg-gray-800 p-4 shadow-md">
            <h2 className="mb-4 text-lg font-semibold text-white">Parameters</h2>
            {/* File Upload */}
            <div className="mb-6">
              <h3 className="text-md mb-2 font-semibold text-white">Data File (.txt)</h3>
              <input
                type="file"
                accept=".txt"
                onChange={handleFileChange}
                className="w-full rounded bg-gray-700 p-2 text-white"
                disabled={isProcessing}
              />
            </div>

            {/* Isotropy Radio - always visible */}
            <div className="mb-4 rounded-lg bg-gray-700 p-4">
              <h4 className="mb-2 text-sm font-semibold text-white">Analysis Mode</h4>
              <div className="mb-2 flex flex-wrap gap-4">
                {[
                  { value: 'isotropy', label: 'Isotropy' },
                  { value: 'anisotropy', label: 'Anisotropy' },
                  { value: 'transverse_anisotropy', label: 'Transverse Anisotropy' },
                ].map((opt) => (
                  <label key={opt.value} className="flex items-center text-white">
                    <input
                      type="radio"
                      name="isotropy"
                      value={opt.value}
                      checked={isotropyOption === opt.value}
                      onChange={() =>
                        handleIsotropyOptionChange(
                          opt.value as 'isotropy' | 'anisotropy' | 'transverse_anisotropy'
                        )
                      }
                      className="mr-2"
                      disabled={isProcessing}
                    />
                    {opt.label}
                  </label>
                ))}
              </div>
            </div>

            {/* Isotropy/Anisotropy form fields */}
            {isotropyOption !== 'transverse_anisotropy' && (
              <>
                {/* Experimental Inputs */}
                <div className="mb-6">
                  <h3 className="text-md mb-2 font-semibold text-white">Experimental Inputs</h3>
                  {/* Lens Magnification */}
                  <div className="mb-4 rounded-lg bg-gray-700 p-4">
                    <h4 className="mb-2 text-sm font-semibold text-white">Lens Magnification</h4>
                    <div className="mb-2 flex space-x-4">
                      {['5x', '10x', '20x', 'custom'].map((opt) => (
                        <label key={opt} className="flex items-center text-white">
                          <input
                            type="radio"
                            name="lens"
                            value={opt}
                            checked={lensOption === opt}
                            onChange={() =>
                              handleLensOptionChange(opt as '5x' | '10x' | '20x' | 'custom')
                            }
                            className="mr-2"
                            disabled={isProcessing}
                          />
                          {opt}
                        </label>
                      ))}
                    </div>
                    {[
                      { field: 'w_rms', label: `W RMS [${fieldUnits.w_rms}]` },
                      {
                        field: 'x_offset',
                        label: `X Offset [${fieldUnits.x_offset}]`,
                      },
                      {
                        field: 'lens_transmittance',
                        label: `Lens Transmittance ${
                          fieldUnits.lens_transmittance ? `[${fieldUnits.lens_transmittance}]` : ''
                        }`,
                      },
                      {
                        field: 'detector_factor',
                        label: `Detector Factor [${fieldUnits.detector_factor}]`,
                      },
                      ...(isotropyOption === 'anisotropy'
                        ? [{ field: 'phi', label: `Phi [${fieldUnits.phi}]` }]
                        : []),
                    ].map((param) => (
                      <div key={param.field} className="mb-2 flex flex-col">
                        <label className="mb-1 text-sm text-white">{param.label}</label>
                        <input
                          type="number"
                          step="any"
                          value={params[param.field as keyof FDPBDParams]}
                          onChange={(e) => handleInputChange(e, param.field as keyof FDPBDParams)}
                          className={`rounded border-2 bg-gray-800 p-2 text-white focus:outline-none ${
                            isValidDecimal(params[param.field as keyof FDPBDParams])
                              ? 'border-gray-600 focus:border-teal-500'
                              : 'border-red-500'
                          }`}
                          disabled={isProcessing}
                          required
                        />
                      </div>
                    ))}
                  </div>
                  {/* Laser */}
                  <div className="rounded-lg bg-gray-700 p-4">
                    <h4 className="mb-2 text-sm font-semibold text-white">Laser</h4>
                    <div className="mb-2 flex space-x-4">
                      {['TOPS 1', 'TOPS 2', 'custom'].map((opt) => (
                        <label key={opt} className="flex items-center text-white">
                          <input
                            type="radio"
                            name="laser"
                            value={opt}
                            checked={laserOption === opt}
                            onChange={() =>
                              handleLaserOptionChange(opt as 'TOPS 1' | 'TOPS 2' | 'custom')
                            }
                            className="mr-2"
                            disabled={isProcessing}
                          />
                          {opt}
                        </label>
                      ))}
                    </div>
                    {[
                      {
                        field: 'f_rolloff',
                        label: `f Rolloff [${fieldUnits.f_rolloff}]`,
                      },
                      {
                        field: 'delay_1',
                        label: `Delay 1 [${fieldUnits.delay_1}]`,
                      },
                      {
                        field: 'delay_2',
                        label: `Delay 2 [${fieldUnits.delay_2}]`,
                      },
                      {
                        field: 'incident_pump',
                        label: `Incident Pump [${fieldUnits.incident_pump}]`,
                      },
                      {
                        field: 'incident_probe',
                        label: `Incident Probe [${fieldUnits.incident_probe}]`,
                      },
                    ].map((param) => (
                      <div key={param.field} className="mb-2 flex flex-col">
                        <label className="mb-1 text-sm text-white">{param.label}</label>
                        <input
                          type="number"
                          step="any"
                          value={params[param.field as keyof FDPBDParams]}
                          onChange={(e) => handleInputChange(e, param.field as keyof FDPBDParams)}
                          className={`rounded border-2 bg-gray-800 p-2 text-white focus:outline-none ${
                            isValidDecimal(params[param.field as keyof FDPBDParams])
                              ? 'border-gray-600 focus:border-teal-500'
                              : 'border-red-500'
                          }`}
                          disabled={isProcessing}
                          required
                        />
                      </div>
                    ))}
                  </div>
                </div>

                {/* Sample Inputs */}
                <div className="mb-6">
                  <h3 className="text-md mb-2 font-semibold text-white">Sample Inputs</h3>
                  {/* Medium */}
                  <div className="mb-4 rounded-lg bg-gray-700 p-4">
                    <h4 className="mb-2 text-sm font-semibold text-white">Medium</h4>
                    <div className="mb-2 flex space-x-4">
                      {['air', 'custom'].map((opt) => (
                        <label key={opt} className="flex items-center text-white">
                          <input
                            type="radio"
                            name="medium"
                            value={opt}
                            checked={mediumOption === opt}
                            onChange={() => handleMediumOptionChange(opt as 'air' | 'custom')}
                            className="mr-2"
                            disabled={isProcessing}
                          />
                          {opt}
                        </label>
                      ))}
                    </div>
                    {[
                      {
                        field: 'lambda_up',
                        label: `Lambda Up [${fieldUnits.lambda_up}]`,
                      },
                      { field: 'c_up', label: `C Up [${fieldUnits.c_up}]` },
                      ...(isotropyOption === 'isotropy'
                        ? [
                            {
                              field: 'eta_up',
                              label: `Eta Up ${fieldUnits.eta_up ? `[${fieldUnits.eta_up}]` : ''}`,
                            },
                            { field: 'h_up', label: `H Up [${fieldUnits.h_up}]` },
                          ]
                        : []),
                    ].map((param) => (
                      <div key={param.field} className="mb-2 flex flex-col">
                        <label className="mb-1 text-sm text-white">{param.label}</label>
                        <input
                          type="number"
                          step="any"
                          value={params[param.field as keyof FDPBDParams]}
                          onChange={(e) => handleInputChange(e, param.field as keyof FDPBDParams)}
                          className={`rounded border-2 bg-gray-800 p-2 text-white focus:outline-none ${
                            isValidDecimal(params[param.field as keyof FDPBDParams])
                              ? 'border-gray-600 focus:border-teal-500'
                              : 'border-red-500'
                          }`}
                          disabled={isProcessing}
                          required
                        />
                      </div>
                    ))}
                  </div>
                  {/* Transducer Layer */}
                  <div className="mb-4 rounded-lg bg-gray-700 p-4">
                    <h4 className="mb-2 text-sm font-semibold text-white">Transducer Layer</h4>
                    <div className="mb-2 flex space-x-4">
                      {['Al', 'custom'].map((opt) => (
                        <label key={opt} className="flex items-center text-white">
                          <input
                            type="radio"
                            name="transducer"
                            value={opt}
                            checked={transducerOption === opt}
                            onChange={() => handleTransducerOptionChange(opt as 'Al' | 'custom')}
                            className="mr-2"
                            disabled={isProcessing}
                          />
                          {opt}
                        </label>
                      ))}
                    </div>
                    {[
                      {
                        field: 'lambda_down',
                        index: 0,
                        label: `Lambda Down [${fieldUnits.lambda_down}]`,
                      },
                      {
                        field: 'c_down',
                        index: 0,
                        label: `C Down [${fieldUnits.c_down}]`,
                      },
                      {
                        field: 'h_down',
                        index: 0,
                        label: `h Down [${fieldUnits.h_down}]`,
                      },
                      ...(isotropyOption === 'isotropy'
                        ? [
                            {
                              field: 'eta_down',
                              index: 0,
                              label: `Eta Down ${
                                fieldUnits.eta_down ? `[${fieldUnits.eta_down}]` : ''
                              }`,
                            },
                          ]
                        : []),
                      {
                        field: 'n_al',
                        label: `Refractive Index (n) ${fieldUnits.n_al ? `[${fieldUnits.n_al}]` : ''}`,
                      },
                      {
                        field: 'k_al',
                        label: `Imaginary Index (k) ${fieldUnits.k_al ? `[${fieldUnits.k_al}]` : ''}`,
                      },
                      ...(isotropyOption === 'anisotropy'
                        ? [
                            { field: 'rho', label: `Rho [${fieldUnits.rho}]` },
                            {
                              field: 'alphaT',
                              label: `Alpha T [${fieldUnits.alphaT}]`,
                            },
                            { field: 'C11_0', label: `C11 [${fieldUnits.C11_0}]` },
                            { field: 'C12_0', label: `C12 [${fieldUnits.C12_0}]` },
                            { field: 'C44_0', label: `C44 [${fieldUnits.C44_0}]` },
                          ]
                        : []),
                    ].map((param) => (
                      <div
                        key={`${param.field}${param.index ?? ''}`}
                        className="mb-2 flex flex-col"
                      >
                        <label className="mb-1 text-sm text-white">{param.label}</label>
                        <input
                          type="number"
                          step="any"
                          value={
                            param.index !== undefined
                              ? params[param.field as keyof FDPBDParams][param.index]
                              : params[param.field as keyof FDPBDParams]
                          }
                          onChange={(e) =>
                            handleInputChange(e, param.field as keyof FDPBDParams, param.index)
                          }
                          className={`rounded border-2 bg-gray-800 p-2 text-white focus:outline-none ${
                            isValidDecimal(
                              param.index !== undefined
                                ? params[param.field as keyof FDPBDParams][param.index]
                                : params[param.field as keyof FDPBDParams]
                            )
                              ? 'border-gray-600 focus:border-teal-500'
                              : 'border-red-500'
                          }`}
                          disabled={isProcessing}
                          required
                        />
                      </div>
                    ))}
                  </div>
                  {/* Interface Layer */}
                  {isotropyOption === 'isotropy' && (
                    <div className="mb-4 rounded-lg bg-gray-700 p-4">
                      <h4 className="mb-2 text-sm font-semibold text-white">Interface Layer</h4>
                      {[
                        {
                          field: 'lambda_down',
                          index: 1,
                          label: `Lambda Down [${fieldUnits.lambda_down}]`,
                        },
                        {
                          field: 'c_down',
                          index: 1,
                          label: `C Down [${fieldUnits.c_down}]`,
                        },
                        {
                          field: 'h_down',
                          index: 1,
                          label: `h Down [${fieldUnits.h_down}]`,
                        },
                        {
                          field: 'eta_down',
                          index: 1,
                          label: `Eta Down ${fieldUnits.eta_down ? `[${fieldUnits.eta_down}]` : ''}`,
                        },
                      ].map((param) => (
                        <div key={`${param.field}${param.index}`} className="mb-2 flex flex-col">
                          <label className="mb-1 text-sm text-white">{param.label}</label>
                          <input
                            type="number"
                            step="any"
                            value={params[param.field as keyof FDPBDParams][param.index]}
                            onChange={(e) =>
                              handleInputChange(e, param.field as keyof FDPBDParams, param.index)
                            }
                            className={`rounded border-2 bg-gray-800 p-2 text-white focus:outline-none ${
                              isValidDecimal(params[param.field as keyof FDPBDParams][param.index])
                                ? 'border-gray-600 focus:border-teal-500'
                                : 'border-red-500'
                            }`}
                            disabled={isProcessing}
                            required
                          />
                        </div>
                      ))}
                    </div>
                  )}
                  {/* Sample Layer */}
                  <div className="mb-4 rounded-lg bg-gray-700 p-4">
                    <h4 className="mb-2 text-sm font-semibold text-white">Sample Layer</h4>
                    {[
                      ...(isotropyOption === 'isotropy'
                        ? [
                            {
                              field: 'lambda_down',
                              index: 2,
                              label: `Lambda Down [${fieldUnits.lambda_down}]`,
                            },
                            {
                              field: 'c_down',
                              index: 2,
                              label: `C Down [${fieldUnits.c_down}]`,
                            },
                            {
                              field: 'h_down',
                              index: 2,
                              label: `h Down [${fieldUnits.h_down}]`,
                            },
                            {
                              field: 'eta_down',
                              index: 2,
                              label: `Eta Down ${
                                fieldUnits.eta_down ? `[${fieldUnits.eta_down}]` : ''
                              }`,
                            },
                            {
                              field: 'alpha_t',
                              label: `Alpha T [${fieldUnits.alpha_t}]`,
                            },
                            {
                              field: 'niu',
                              label: `Niu ${fieldUnits.niu ? `[${fieldUnits.niu}]` : ''}`,
                            },
                          ]
                        : [
                            {
                              field: 'lambda_down_x_sample',
                              label: `Lambda Down X [${fieldUnits.lambda_down_x_sample}]`,
                            },
                            {
                              field: 'lambda_down_y_sample',
                              label: `Lambda Down Y [${fieldUnits.lambda_down_y_sample}]`,
                            },
                            {
                              field: 'lambda_down_z_sample',
                              label: `Lambda Down Z [${fieldUnits.lambda_down_z_sample}]`,
                            },
                            {
                              field: 'c_down',
                              index: 2,
                              label: `C Down [${fieldUnits.c_down}]`,
                            },
                            {
                              field: 'rho_sample',
                              label: `Rho [${fieldUnits.rho_sample}]`,
                            },
                            {
                              field: 'C11_0_sample',
                              label: `C11 [${fieldUnits.C11_0_sample}]`,
                            },
                            {
                              field: 'C12_0_sample',
                              label: `C12 [${fieldUnits.C12_0_sample}]`,
                            },
                            {
                              field: 'C13_0_sample',
                              label: `C13 [${fieldUnits.C13_0_sample}]`,
                            },
                            {
                              field: 'C33_0_sample',
                              label: `C33 [${fieldUnits.C33_0_sample}]`,
                            },
                            {
                              field: 'C44_0_sample',
                              label: `C44 [${fieldUnits.C44_0_sample}]`,
                            },
                            {
                              field: 'alphaT_perp',
                              label: `Alpha T Perpendicular [${fieldUnits.alphaT_perp}]`,
                            },
                            {
                              field: 'alphaT_para',
                              label: `Alpha T Parallel [${fieldUnits.alphaT_para}]`,
                            },
                          ]),
                    ].map((param) => (
                      <div
                        key={`${param.field}${param.index ?? ''}`}
                        className="mb-2 flex flex-col"
                      >
                        <label className="mb-1 text-sm text-white">{param.label}</label>
                        <input
                          type="number"
                          step="any"
                          value={
                            param.index !== undefined
                              ? params[param.field as keyof FDPBDParams][param.index]
                              : params[param.field as keyof FDPBDParams]
                          }
                          onChange={(e) =>
                            handleInputChange(e, param.field as keyof FDPBDParams, param.index)
                          }
                          className={`rounded border-2 bg-gray-800 p-2 text-white focus:outline-none ${
                            isValidDecimal(
                              param.index !== undefined
                                ? params[param.field as keyof FDPBDParams][param.index]
                                : params[param.field as keyof FDPBDParams]
                            )
                              ? 'border-gray-600 focus:border-teal-500'
                              : 'border-red-500'
                          }`}
                          disabled={isProcessing}
                          required
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Transverse Anisotropy form fields */}
            {isotropyOption === 'transverse_anisotropy' && (
              <>
                <div className="mb-6">
                  <h3 className="text-md mb-2 font-semibold text-white">Experimental Inputs</h3>
                  {/* Lens Magnification */}
                  <div className="mb-4 rounded-lg bg-gray-700 p-4">
                    <h4 className="mb-2 text-sm font-semibold text-white">Lens Magnification</h4>
                    <div className="mb-2 flex space-x-4">
                      {['5x', '10x', '20x', 'custom'].map((opt) => (
                        <label key={opt} className="flex items-center text-white">
                          <input
                            type="radio"
                            name="lens_transverse"
                            value={opt}
                            checked={lensOption === opt}
                            onChange={() =>
                              handleLensOptionChange(opt as '5x' | '10x' | '20x' | 'custom')
                            }
                            className="mr-2"
                            disabled={isProcessing}
                          />
                          {opt}
                        </label>
                      ))}
                    </div>
                    {[
                      { field: 'w_rms', label: `W RMS [${fieldUnits.w_rms}]` },
                      { field: 'x_offset', label: `X Offset [${fieldUnits.x_offset}]` },
                      { field: 'lens_transmittance', label: 'Lens Transmittance' },
                      {
                        field: 'detector_factor',
                        label: `Detector Factor [${fieldUnits.detector_factor}]`,
                      },
                      { field: 'v_sum_fixed', label: `V Sum Fixed [${fieldUnits.v_sum_fixed}]` },
                      { field: 'c_probe', label: 'C Probe' },
                    ].map((param) => (
                      <div key={param.field} className="mb-2 flex flex-col">
                        <label className="mb-1 text-sm text-white">{param.label}</label>
                        <input
                          type="number"
                          step="any"
                          value={params[param.field as keyof FDPBDParams]}
                          onChange={(e) => handleInputChange(e, param.field as keyof FDPBDParams)}
                          className={`rounded border-2 bg-gray-800 p-2 text-white focus:outline-none ${
                            isValidDecimal(params[param.field as keyof FDPBDParams])
                              ? 'border-gray-600 focus:border-teal-500'
                              : 'border-red-500'
                          }`}
                          disabled={isProcessing}
                          required
                        />
                      </div>
                    ))}
                  </div>

                  {/* Laser */}
                  <div className="mb-4 rounded-lg bg-gray-700 p-4">
                    <h4 className="mb-2 text-sm font-semibold text-white">Laser</h4>
                    <div className="mb-2 flex space-x-4">
                      {['TOPS 1', 'TOPS 2', 'custom'].map((opt) => (
                        <label key={opt} className="flex items-center text-white">
                          <input
                            type="radio"
                            name="laser_transverse"
                            value={opt}
                            checked={laserOption === opt}
                            onChange={() =>
                              handleLaserOptionChange(opt as 'TOPS 1' | 'TOPS 2' | 'custom')
                            }
                            className="mr-2"
                            disabled={isProcessing}
                          />
                          {opt}
                        </label>
                      ))}
                    </div>
                    {[
                      { field: 'f_rolloff', label: `f Rolloff [${fieldUnits.f_rolloff}]` },
                      { field: 'delay_1', label: `Delay 1 [${fieldUnits.delay_1}]` },
                      { field: 'delay_2', label: `Delay 2 [${fieldUnits.delay_2}]` },
                      {
                        field: 'incident_pump',
                        label: `Incident Pump [${fieldUnits.incident_pump}]`,
                      },
                    ].map((param) => (
                      <div key={param.field} className="mb-2 flex flex-col">
                        <label className="mb-1 text-sm text-white">{param.label}</label>
                        <input
                          type="number"
                          step="any"
                          value={params[param.field as keyof FDPBDParams]}
                          onChange={(e) => handleInputChange(e, param.field as keyof FDPBDParams)}
                          className={`rounded border-2 bg-gray-800 p-2 text-white focus:outline-none ${
                            isValidDecimal(params[param.field as keyof FDPBDParams])
                              ? 'border-gray-600 focus:border-teal-500'
                              : 'border-red-500'
                          }`}
                          disabled={isProcessing}
                          required
                        />
                      </div>
                    ))}
                  </div>
                </div>

                {/* Sample Inputs */}
                <div className="mb-6">
                  <h3 className="text-md mb-2 font-semibold text-white">Sample Inputs</h3>

                  {/* Medium (Air / Layer 3) */}
                  <div className="mb-4 rounded-lg bg-gray-700 p-4">
                    <h4 className="mb-2 text-sm font-semibold text-white">Medium</h4>
                    <div className="mb-2 flex space-x-4">
                      {['air', 'custom'].map((opt) => (
                        <label key={opt} className="flex items-center text-white">
                          <input
                            type="radio"
                            name="medium_transverse"
                            value={opt}
                            checked={mediumOption === opt}
                            onChange={() => handleMediumOptionChange(opt as 'air' | 'custom')}
                            className="mr-2"
                            disabled={isProcessing}
                          />
                          {opt}
                        </label>
                      ))}
                    </div>
                    {[
                      {
                        field: 'lambda_up',
                        label: `Thermal Conductivity [${fieldUnits.lambda_up}]`,
                      },
                      { field: 'c_up', label: `Heat Capacity [${fieldUnits.c_up}]` },
                    ].map((param) => (
                      <div key={param.field} className="mb-2 flex flex-col">
                        <label className="mb-1 text-sm text-white">{param.label}</label>
                        <input
                          type="number"
                          step="any"
                          value={params[param.field as keyof FDPBDParams]}
                          onChange={(e) => handleInputChange(e, param.field as keyof FDPBDParams)}
                          className={`rounded border-2 bg-gray-800 p-2 text-white focus:outline-none ${
                            isValidDecimal(params[param.field as keyof FDPBDParams])
                              ? 'border-gray-600 focus:border-teal-500'
                              : 'border-red-500'
                          }`}
                          disabled={isProcessing}
                          required
                        />
                      </div>
                    ))}
                  </div>

                  {/* Transducer Layer (Al Film / Layer 1) */}
                  <div className="mb-4 rounded-lg bg-gray-700 p-4">
                    <h4 className="mb-2 text-sm font-semibold text-white">
                      Transducer Layer (Al Film)
                    </h4>
                    <div className="mb-2 flex space-x-4">
                      {['Al', 'custom'].map((opt) => (
                        <label key={opt} className="flex items-center text-white">
                          <input
                            type="radio"
                            name="transducer_transverse"
                            value={opt}
                            checked={transducerOption === opt}
                            onChange={() => handleTransducerOptionChange(opt as 'Al' | 'custom')}
                            className="mr-2"
                            disabled={isProcessing}
                          />
                          {opt}
                        </label>
                      ))}
                    </div>
                    {[
                      {
                        field: 'lambda_down',
                        index: 0,
                        label: `Thermal Conductivity [${fieldUnits.lambda_down}]`,
                      },
                      { field: 'c_down', index: 0, label: `Heat Capacity [${fieldUnits.c_down}]` },
                      { field: 'h_down', index: 0, label: `Thickness [${fieldUnits.h_down}]` },
                      { field: 'n_al', label: 'Refractive Index (n)' },
                      { field: 'k_al', label: 'Imaginary Index (k)' },
                      { field: 'rho', label: `Density [${fieldUnits.rho}]` },
                      { field: 'alphaT', label: `CTE [${fieldUnits.alphaT}]` },
                      { field: 'C11_0', label: `C11 [${fieldUnits.C11_0}]` },
                      { field: 'C12_0', label: `C12 [${fieldUnits.C12_0}]` },
                      { field: 'C44_0', label: `C44 [${fieldUnits.C44_0}]` },
                      {
                        field: 'g_int',
                        label: `Thermal Boundary Conductance [${fieldUnits.g_int}]`,
                      },
                    ].map((param) => (
                      <div
                        key={`${param.field}${param.index ?? ''}`}
                        className="mb-2 flex flex-col"
                      >
                        <label className="mb-1 text-sm text-white">{param.label}</label>
                        <input
                          type="number"
                          step="any"
                          value={
                            param.index !== undefined
                              ? params[param.field as keyof FDPBDParams][param.index]
                              : params[param.field as keyof FDPBDParams]
                          }
                          onChange={(e) =>
                            handleInputChange(e, param.field as keyof FDPBDParams, param.index)
                          }
                          className={`rounded border-2 bg-gray-800 p-2 text-white focus:outline-none ${
                            isValidDecimal(
                              param.index !== undefined
                                ? params[param.field as keyof FDPBDParams][param.index]
                                : params[param.field as keyof FDPBDParams]
                            )
                              ? 'border-gray-600 focus:border-teal-500'
                              : 'border-red-500'
                          }`}
                          disabled={isProcessing}
                          required
                        />
                      </div>
                    ))}
                  </div>

                  {/* Sample Layer (Bulk / Layer 2) */}
                  <div className="mb-4 rounded-lg bg-gray-700 p-4">
                    <h4 className="mb-2 text-sm font-semibold text-white">Sample Layer (Bulk)</h4>
                    {[
                      {
                        field: 'lambda_down_x_sample',
                        label: `In-plane Conductivity [${fieldUnits.lambda_down_x_sample}]`,
                      },
                      {
                        field: 'lambda_down_z_sample',
                        label: `Through-plane Conductivity [${fieldUnits.lambda_down_z_sample}]`,
                      },
                      { field: 'c_down', index: 2, label: `Heat Capacity [${fieldUnits.c_down}]` },
                      { field: 'rho_sample', label: `Density [${fieldUnits.rho_sample}]` },
                      { field: 'alphaT_perp', label: `CTE In-plane [${fieldUnits.alphaT_perp}]` },
                      {
                        field: 'alphaT_para',
                        label: `CTE Through-plane [${fieldUnits.alphaT_para}]`,
                      },
                      { field: 'C11_0_sample', label: `C11 [${fieldUnits.C11_0_sample}]` },
                      { field: 'C12_0_sample', label: `C12 [${fieldUnits.C12_0_sample}]` },
                      { field: 'C13_0_sample', label: `C13 [${fieldUnits.C13_0_sample}]` },
                      { field: 'C33_0_sample', label: `C33 [${fieldUnits.C33_0_sample}]` },
                      { field: 'C44_0_sample', label: `C44 [${fieldUnits.C44_0_sample}]` },
                    ].map((param) => (
                      <div
                        key={`${param.field}${param.index ?? ''}`}
                        className="mb-2 flex flex-col"
                      >
                        <label className="mb-1 text-sm text-white">{param.label}</label>
                        <input
                          type="number"
                          step="any"
                          value={
                            param.index !== undefined
                              ? params[param.field as keyof FDPBDParams][param.index]
                              : params[param.field as keyof FDPBDParams]
                          }
                          onChange={(e) =>
                            handleInputChange(e, param.field as keyof FDPBDParams, param.index)
                          }
                          className={`rounded border-2 bg-gray-800 p-2 text-white focus:outline-none ${
                            isValidDecimal(
                              param.index !== undefined
                                ? params[param.field as keyof FDPBDParams][param.index]
                                : params[param.field as keyof FDPBDParams]
                            )
                              ? 'border-gray-600 focus:border-teal-500'
                              : 'border-red-500'
                          }`}
                          disabled={isProcessing}
                          required
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Buttons */}
            <div className="flex space-x-4">
              <button
                onClick={handleSubmit}
                disabled={isProcessing || !isFormValid()}
                className={`flex-1 rounded py-2 text-white ${
                  isProcessing || !isFormValid()
                    ? 'cursor-not-allowed bg-gray-600'
                    : 'bg-teal-500 hover:bg-teal-600'
                }`}
              >
                {isProcessing ? 'Processing...' : 'Run Analysis'}
              </button>
              <button
                onClick={handleClear}
                className="flex-1 rounded bg-gray-500 py-2 text-white hover:bg-gray-600"
                disabled={isProcessing}
              >
                Clear
              </button>
            </div>
            {status && (
              <p
                className={`mt-2 text-sm ${
                  status.includes('Error') ? 'text-red-400' : 'text-green-400'
                }`}
              >
                {status}
              </p>
            )}
          </div>
        </div>

        {/* Right Panel: Results and Graphs */}
        <div className="flex w-2/3 flex-col space-y-4">
          {result && (
            <>
              <div className="rounded-lg bg-gray-800 p-4 shadow-md">
                <h2 className="mb-4 text-lg font-semibold text-white">Results</h2>
                {result && (
                  <>
                    {isotropyOption === 'isotropy' &&
                      (() => {
                        const isotropicResult = result as FDPBDResult;
                        return (
                          <>
                            <p className="text-white">
                              Thermal Conductivity: {isotropicResult.lambda_measure.toFixed(3)}{' '}
                              W/m-K
                            </p>
                            <p className="text-white">
                              Thermal Expansion: {isotropicResult.alpha_t_fitted.toExponential(3)}{' '}
                              /K
                            </p>
                          </>
                        );
                      })()}
                    {isotropyOption === 'anisotropy' &&
                      (() => {
                        const anisotropicResult = result as AnisotropicFDPBDResult;
                        return (
                          <>
                            <p className="text-white">
                              Peak Frequency:{' '}
                              {anisotropicResult.f_peak
                                ? anisotropicResult.f_peak.toFixed(2)
                                : 'N/A'}{' '}
                              Hz
                            </p>
                            <p className="text-white">
                              Ratio at Peak:{' '}
                              {anisotropicResult.ratio_at_peak
                                ? anisotropicResult.ratio_at_peak.toFixed(4)
                                : 'N/A'}
                            </p>
                          </>
                        );
                      })()}
                    {isotropyOption === 'transverse_anisotropy' && (
                      <p className="text-white">
                        Forward model complete. Compare model vs experimental data in the plots
                        below.
                      </p>
                    )}
                  </>
                )}
              </div>
              <div className="rounded-lg bg-gray-800 p-4 shadow-md">
                <h2 className="mb-4 text-lg font-semibold text-white">Graphs</h2>
                <div className="flex flex-col space-y-4">
                  {isotropyOption === 'isotropy' && result && (
                    <>
                      <Plot
                        data={[
                          {
                            x: (result as FDPBDResult).plot_data.freq_fit,
                            y: (result as FDPBDResult).plot_data.v_corr_in_fit,
                            type: 'scatter',
                            mode: 'markers',
                            name: 'In-phase (data)',
                            marker: { color: 'black' },
                          },
                          {
                            x: (result as FDPBDResult).plot_data.freq_fit,
                            y: (result as FDPBDResult).plot_data.v_corr_out_fit,
                            type: 'scatter',
                            mode: 'markers',
                            name: 'Out-of-phase (data)',
                            marker: { color: 'black' },
                          },
                          {
                            x: (result as FDPBDResult).plot_data.freq_fit,
                            y: (result as FDPBDResult).plot_data.delta_in,
                            type: 'scatter',
                            mode: 'lines',
                            name: 'In-phase (model)',
                            line: { color: 'blue' },
                          },
                          {
                            x: (result as FDPBDResult).plot_data.freq_fit,
                            y: (result as FDPBDResult).plot_data.delta_out,
                            type: 'scatter',
                            mode: 'lines',
                            name: 'Out-of-phase (model)',
                            line: { color: 'red' },
                          },
                        ]}
                        layout={{
                          title: 'In/Out-of-phase',
                          xaxis: {
                            title: {
                              text: 'Frequency (Hz)',
                              font: { size: 14, color: 'black' },
                              standoff: 10,
                            },
                            type: 'log',
                            showgrid: false,
                            tickfont: { size: 12, color: 'black' },
                            showticklabels: true,
                            tickmode: 'auto',
                            nticks: 3,
                          },
                          yaxis: {
                            title: {
                              text: 'In/Out-of-phase (V)',
                              font: { size: 14, color: 'black' },
                              standoff: 10,
                            },
                            showgrid: false,
                            tickfont: { size: 12, color: 'black' },
                            showticklabels: true,
                            tickmode: 'auto',
                            nticks: 5,
                          },
                          legend: { x: 1, xanchor: 'right', y: 1 },
                          plot_bgcolor: 'white',
                          paper_bgcolor: 'white',
                          font: { color: 'black' },
                          width: 800,
                          height: 400,
                          margin: { l: 60, r: 40, t: 60, b: 60 },
                          shapes: [
                            {
                              type: 'rect',
                              xref: 'paper',
                              yref: 'paper',
                              x0: 0,
                              y0: 0,
                              x1: 1,
                              y1: 1,
                              line: { color: 'black', width: 2 },
                            },
                          ],
                        }}
                      />
                      <Plot
                        data={[
                          {
                            x: (result as FDPBDResult).plot_data.freq_fit,
                            y: (result as FDPBDResult).plot_data.v_corr_ratio_fit,
                            type: 'scatter',
                            mode: 'markers',
                            name: 'Ratio (data)',
                            marker: { color: 'black' },
                          },
                          {
                            x: (result as FDPBDResult).plot_data.freq_fit,
                            y: (result as FDPBDResult).plot_data.delta_ratio,
                            type: 'scatter',
                            mode: 'lines',
                            name: 'Ratio (model)',
                            line: { color: 'blue' },
                          },
                        ]}
                        layout={{
                          title: 'Ratio',
                          xaxis: {
                            title: {
                              text: 'Frequency (Hz)',
                              font: { size: 14, color: 'black' },
                              standoff: 10,
                            },
                            type: 'log',
                            showgrid: false,
                            tickfont: { size: 12, color: 'black' },
                            showticklabels: true,
                            tickmode: 'auto',
                            nticks: 3,
                          },
                          yaxis: {
                            title: {
                              text: 'Ratio',
                              font: { size: 14, color: 'black' },
                              standoff: 10,
                            },
                            type: 'log',
                            showgrid: false,
                            tickfont: { size: 12, color: 'black' },
                            showticklabels: true,
                            tickmode: 'auto',
                            nticks: 5,
                          },
                          legend: { x: 1, xanchor: 'right', y: 1 },
                          plot_bgcolor: 'white',
                          paper_bgcolor: 'white',
                          font: { color: 'black' },
                          width: 800,
                          height: 400,
                          margin: { l: 60, r: 40, t: 60, b: 60 },
                          shapes: [
                            {
                              type: 'rect',
                              xref: 'paper',
                              yref: 'paper',
                              x0: 0,
                              y0: 0,
                              x1: 1,
                              y1: 1,
                              line: { color: 'black', width: 2 },
                            },
                          ],
                        }}
                      />
                    </>
                  )}
                  {isotropyOption === 'anisotropy' && result && (
                    <>
                      <Plot
                        data={[
                          {
                            x: (result as AnisotropicFDPBDResult).plot_data.exp_freqs,
                            y: (result as AnisotropicFDPBDResult).plot_data.in_exp,
                            type: 'scatter',
                            mode: 'markers',
                            name: 'In-phase (data)',
                            marker: { color: 'black' },
                          },
                          {
                            x: (result as AnisotropicFDPBDResult).plot_data.exp_freqs,
                            y: (result as AnisotropicFDPBDResult).plot_data.out_exp,
                            type: 'scatter',
                            mode: 'markers',
                            name: 'Out-of-phase (data)',
                            marker: { color: 'black' },
                          },
                          {
                            x: (result as AnisotropicFDPBDResult).plot_data.model_freqs,
                            y: (result as AnisotropicFDPBDResult).plot_data.in_model,
                            type: 'scatter',
                            mode: 'lines',
                            name: 'In-phase (model)',
                            line: { color: 'blue' },
                          },
                          {
                            x: (result as AnisotropicFDPBDResult).plot_data.model_freqs,
                            y: (result as AnisotropicFDPBDResult).plot_data.out_model,
                            type: 'scatter',
                            mode: 'lines',
                            name: 'Out-of-phase (model)',
                            line: { color: 'red' },
                          },
                        ]}
                        layout={{
                          title: 'In/Out-of-phase',
                          xaxis: {
                            title: {
                              text: 'Frequency (Hz)',
                              font: { size: 14, color: 'black' },
                              standoff: 10,
                            },
                            type: 'log',
                            showgrid: false,
                            tickfont: { size: 12, color: 'black' },
                            showticklabels: true,
                            tickmode: 'auto',
                            nticks: 3,
                          },
                          yaxis: {
                            title: {
                              text: 'In/Out-of-phase (V)',
                              font: { size: 14, color: 'black' },
                              standoff: 10,
                            },
                            showgrid: false,
                            tickfont: { size: 12, color: 'black' },
                            showticklabels: true,
                            tickmode: 'auto',
                            nticks: 5,
                          },
                          legend: { x: 1, xanchor: 'right', y: 1 },
                          plot_bgcolor: 'white',
                          paper_bgcolor: 'white',
                          font: { color: 'black' },
                          width: 800,
                          height: 400,
                          margin: { l: 60, r: 40, t: 60, b: 60 },
                          shapes: [
                            {
                              type: 'rect',
                              xref: 'paper',
                              yref: 'paper',
                              x0: 0,
                              y0: 0,
                              x1: 1,
                              y1: 1,
                              line: { color: 'black', width: 2 },
                            },
                          ],
                        }}
                      />
                      <Plot
                        data={[
                          {
                            x: (result as AnisotropicFDPBDResult).plot_data.exp_freqs,
                            y: (result as AnisotropicFDPBDResult).plot_data.ratio_exp,
                            type: 'scatter',
                            mode: 'markers',
                            name: 'Ratio (data)',
                            marker: { color: 'black' },
                          },
                          {
                            x: (result as AnisotropicFDPBDResult).plot_data.model_freqs,
                            y: (result as AnisotropicFDPBDResult).plot_data.ratio_model,
                            type: 'scatter',
                            mode: 'lines',
                            name: 'Ratio (model)',
                            line: { color: 'blue' },
                          },
                        ]}
                        layout={{
                          title: 'Ratio',
                          xaxis: {
                            title: {
                              text: 'Frequency (Hz)',
                              font: { size: 14, color: 'black' },
                              standoff: 10,
                            },
                            type: 'log',
                            showgrid: false,
                            tickfont: { size: 12, color: 'black' },
                            showticklabels: true,
                            tickmode: 'auto',
                            nticks: 3,
                          },
                          yaxis: {
                            title: {
                              text: 'Ratio',
                              font: { size: 14, color: 'black' },
                              standoff: 10,
                            },
                            type: 'log',
                            showgrid: false,
                            tickfont: { size: 12, color: 'black' },
                            showticklabels: true,
                            tickmode: 'auto',
                            nticks: 5,
                          },
                          legend: { x: 1, xanchor: 'right', y: 1 },
                          plot_bgcolor: 'white',
                          paper_bgcolor: 'white',
                          font: { color: 'black' },
                          width: 800,
                          height: 400,
                          margin: { l: 60, r: 40, t: 60, b: 60 },
                          shapes: [
                            {
                              type: 'rect',
                              xref: 'paper',
                              yref: 'paper',
                              x0: 0,
                              y0: 0,
                              x1: 1,
                              y1: 1,
                              line: { color: 'black', width: 2 },
                            },
                          ],
                        }}
                      />
                    </>
                  )}
                  {isotropyOption === 'transverse_anisotropy' && result && (
                    <>
                      <Plot
                        data={[
                          {
                            x: (result as TransverseIsotropicResult).plot_data.exp_freqs,
                            y: (result as TransverseIsotropicResult).plot_data.in_exp,
                            type: 'scatter',
                            mode: 'markers',
                            name: 'In-phase (data)',
                            marker: { color: 'red' },
                          },
                          {
                            x: (result as TransverseIsotropicResult).plot_data.exp_freqs,
                            y: (result as TransverseIsotropicResult).plot_data.out_exp,
                            type: 'scatter',
                            mode: 'markers',
                            name: 'Out-of-phase (data)',
                            marker: { color: 'red', symbol: 'x' },
                          },
                          {
                            x: (result as TransverseIsotropicResult).plot_data.model_freqs,
                            y: (result as TransverseIsotropicResult).plot_data.in_model,
                            type: 'scatter',
                            mode: 'lines+markers',
                            name: 'In-phase (model)',
                            line: { color: 'black', dash: 'dash' },
                            marker: { color: 'black' },
                          },
                          {
                            x: (result as TransverseIsotropicResult).plot_data.model_freqs,
                            y: (result as TransverseIsotropicResult).plot_data.out_model,
                            type: 'scatter',
                            mode: 'lines+markers',
                            name: 'Out-of-phase (model)',
                            line: { color: 'black', dash: 'dash' },
                            marker: { color: 'black', symbol: 'x' },
                          },
                        ]}
                        layout={{
                          title: 'In/Out-of-phase (Transverse Anisotropy)',
                          xaxis: {
                            title: {
                              text: 'Frequency (Hz)',
                              font: { size: 14, color: 'black' },
                              standoff: 10,
                            },
                            type: 'log',
                            showgrid: true,
                            gridcolor: '#ddd',
                            tickfont: { size: 12, color: 'black' },
                          },
                          yaxis: {
                            title: {
                              text: 'Signal (V)',
                              font: { size: 14, color: 'black' },
                              standoff: 10,
                            },
                            showgrid: true,
                            gridcolor: '#ddd',
                            tickfont: { size: 12, color: 'black' },
                          },
                          legend: { x: 1, xanchor: 'right', y: 1 },
                          plot_bgcolor: 'white',
                          paper_bgcolor: 'white',
                          font: { color: 'black' },
                          width: 800,
                          height: 400,
                          margin: { l: 60, r: 40, t: 60, b: 60 },
                          shapes: [
                            {
                              type: 'rect',
                              xref: 'paper',
                              yref: 'paper',
                              x0: 0,
                              y0: 0,
                              x1: 1,
                              y1: 1,
                              line: { color: 'black', width: 2 },
                            },
                          ],
                        }}
                      />
                      <Plot
                        data={[
                          {
                            x: (result as TransverseIsotropicResult).plot_data.exp_freqs,
                            y: (result as TransverseIsotropicResult).plot_data.ratio_exp,
                            type: 'scatter',
                            mode: 'markers',
                            name: 'Ratio (data)',
                            marker: { color: 'red' },
                          },
                          {
                            x: (result as TransverseIsotropicResult).plot_data.model_freqs,
                            y: (result as TransverseIsotropicResult).plot_data.ratio_model,
                            type: 'scatter',
                            mode: 'lines+markers',
                            name: 'Ratio (model)',
                            line: { color: 'black', dash: 'dash' },
                            marker: { color: 'black' },
                          },
                        ]}
                        layout={{
                          title: 'Ratio (Transverse Anisotropy)',
                          xaxis: {
                            title: {
                              text: 'Frequency (Hz)',
                              font: { size: 14, color: 'black' },
                              standoff: 10,
                            },
                            type: 'log',
                            showgrid: true,
                            gridcolor: '#ddd',
                            tickfont: { size: 12, color: 'black' },
                          },
                          yaxis: {
                            title: {
                              text: 'Ratio',
                              font: { size: 14, color: 'black' },
                              standoff: 10,
                            },
                            type: 'log',
                            showgrid: true,
                            gridcolor: '#ddd',
                            tickfont: { size: 12, color: 'black' },
                          },
                          legend: { x: 1, xanchor: 'right', y: 1 },
                          plot_bgcolor: 'white',
                          paper_bgcolor: 'white',
                          font: { color: 'black' },
                          width: 800,
                          height: 400,
                          margin: { l: 60, r: 40, t: 60, b: 60 },
                          shapes: [
                            {
                              type: 'rect',
                              xref: 'paper',
                              yref: 'paper',
                              x0: 0,
                              y0: 0,
                              x1: 1,
                              y1: 1,
                              line: { color: 'black', width: 2 },
                            },
                          ],
                        }}
                      />
                    </>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="flex justify-between bg-gray-800 p-2 text-sm text-white">
        <div>Status: {status || 'Idle'}</div>
        <div>{new Date().toLocaleString()}</div>
      </footer>
    </div>
  );
}
