'use client';

import { useState } from 'react';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { API_BASE } from '../../lib/api';
import {
  TOPS1_DEFAULTS,
  TOPS2_DEFAULTS,
  LASER_DEFAULTS_PATH,
  type LaserOption,
} from './laserDefaults';

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
  delay_0: string;
  delay_1: string;
  delay_2: string;
  amplitude_corrected_0: string;
  amplitude_corrected_1: string;
  amplitude_corrected_2: string;
  amplitude_corrected_3: string;
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
  focal_length: string;
  w_probe_det: string;
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
  include_air_deflection: boolean;
  dndt_up: string;
};

export default function FDPBDPage() {
  const [params, setParams] = useState<FDPBDParams>({
    delay_0: TOPS1_DEFAULTS.delay_0,
    delay_1: TOPS1_DEFAULTS.delay_1,
    delay_2: TOPS1_DEFAULTS.delay_2,
    amplitude_corrected_0: TOPS1_DEFAULTS.amplitude_corrected_0,
    amplitude_corrected_1: TOPS1_DEFAULTS.amplitude_corrected_1,
    amplitude_corrected_2: TOPS1_DEFAULTS.amplitude_corrected_2,
    amplitude_corrected_3: TOPS1_DEFAULTS.amplitude_corrected_3,
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
    w_rms: '28.00',
    x_offset: '31.50',
    incident_pump: '1.06',
    incident_probe: '0.85',
    n_al: '2.9',
    k_al: '8.2',
    lens_transmittance: '0.86',
    focal_length: '100',
    w_probe_det: '0.971',
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
    c_probe: '0.70',
    g_int: '100e6',
    include_air_deflection: false,
    dndt_up: '-8.9e-7',
  });
  const fieldUnits: Record<string, string> = {
    delay_0: '',
    delay_1: 's',
    delay_2: 's²',
    amplitude_corrected_0: '',
    amplitude_corrected_1: '',
    amplitude_corrected_2: '',
    amplitude_corrected_3: '',
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
    focal_length: 'mm',
    w_probe_det: 'mm',
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
  const [timeTaken, setTimeTaken] = useState<number | null>(null);
  const [resultSource, setResultSource] = useState<'analysis' | 'fit' | null>(null);
  const [isFitting, setIsFitting] = useState(false);
  const [plotExportFormat, setPlotExportFormat] = useState<'svg' | 'png' | 'jpeg' | 'webp'>('svg');
  const [activeTab, setActiveTab] = useState<'forward' | 'fitting'>('forward');
  const [collapsedSections, setCollapsedSections] = useState<Set<string>>(new Set());

  const toggleSection = (section: string) => {
    setCollapsedSections((prev) => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  };
  const [fitParam, setFitParam] = useState('');
  const [fitBoundsMin, setFitBoundsMin] = useState('');
  const [fitBoundsMax, setFitBoundsMax] = useState('');
  const [fitMaxIter, setFitMaxIter] = useState('20');
  const [fitPopSize, setFitPopSize] = useState('8');
  const [fitTol, setFitTol] = useState('1e-3');
  const [fitProgress, setFitProgress] = useState<{
    generation: number;
    best_value: number;
    convergence: number;
    elapsed: number;
  } | null>(null);
  const [fitResult, setFitResult] = useState<{
    best_value: number;
    cost: number;
    generations: number;
    elapsed: number;
    fit_param: string;
  } | null>(null);
  const [lensOption, setLensOption] = useState<'2x' | '5x' | '10x' | '20x' | 'custom'>('2x');
  const [mediumOption, setMediumOption] = useState<'air' | 'custom'>('air');
  const [isotropyOption, setIsotropyOption] = useState<
    'isotropy' | 'anisotropy' | 'transverse_anisotropy'
  >('isotropy');
  const [laserOption, setLaserOption] = useState<LaserOption>('TOPS 1');

  const isValidDecimal = (value: string | string[]) => {
    if (Array.isArray(value)) {
      return value.every((v) => v !== '' && !isNaN(parseFloat(v)));
    }
    return value !== '' && !isNaN(parseFloat(value));
  };

  const activeLeakingFields = (): string[] => [
    params.amplitude_corrected_0,
    params.amplitude_corrected_1,
    params.amplitude_corrected_2,
    params.amplitude_corrected_3,
    params.delay_0,
    params.delay_1,
    params.delay_2,
  ];

  const isFormValid = () => {
    if (isotropyOption === 'transverse_anisotropy') {
      const fields = [
        ...activeLeakingFields(),
        params.incident_pump,
        params.v_sum_fixed,
        params.w_rms,
        params.x_offset,
        params.lens_transmittance,
        params.w_probe_det,
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
      ...activeLeakingFields(),
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
      ...(isotropyOption === 'isotropy' ? [params.niu, params.alpha_t] : []),
      params.lambda_up,
      ...(isotropyOption === 'isotropy' ? [params.eta_up] : []),
      params.c_up,
      params.w_rms,
      params.x_offset,
      params.incident_pump,
      params.incident_probe,
      params.n_al,
      params.k_al,
      params.lens_transmittance,
      params.w_probe_det,
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
        const updatedArray = [...(prev[field] as string[])];
        updatedArray[index] = value;
        return { ...prev, [field]: updatedArray };
      }
      return { ...prev, [field]: value };
    });

    if (['w_rms', 'x_offset', 'lens_transmittance', 'focal_length', 'phi'].includes(field)) {
      const lensValues = {
        '2x': {
          w_rms: '28.00',
          x_offset: '31.50',
          lens_transmittance: '0.86',
          focal_length: '100',
          phi: '0',
        },
        '5x': {
          w_rms: '11.20',
          x_offset: '12.60',
          lens_transmittance: '0.93',
          focal_length: '40',
          phi: '0',
        },
        '10x': {
          w_rms: '5.60',
          x_offset: '6.30',
          lens_transmittance: '0.85',
          focal_length: '20',
          phi: '0',
        },
        '20x': {
          w_rms: '2.825',
          x_offset: '3.15',
          lens_transmittance: '0.80',
          focal_length: '10',
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
            vals.focal_length === updatedParams.focal_length &&
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
              [field]: [
                ...(params[field] as string[]).slice(0, index),
                value,
                ...(params[field] as string[]).slice(index + 1),
              ],
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
  };

  const handleLensOptionChange = (option: '2x' | '5x' | '10x' | '20x' | 'custom') => {
    setLensOption(option);
    if (option !== 'custom') {
      const values = {
        '2x': {
          w_rms: '28.00',
          x_offset: '31.50',
          lens_transmittance: '0.86',
          focal_length: '100',
          phi: '0',
        },
        '5x': {
          w_rms: '11.20',
          x_offset: '12.60',
          lens_transmittance: '0.93',
          focal_length: '40',
          phi: '0',
        },
        '10x': {
          w_rms: '5.60',
          x_offset: '6.30',
          lens_transmittance: '0.85',
          focal_length: '20',
          phi: '0',
        },
        '20x': {
          w_rms: '2.825',
          x_offset: '3.15',
          lens_transmittance: '0.80',
          focal_length: '10',
          phi: '0',
        },
      };
      setParams((prev) => ({
        ...prev,
        w_rms: values[option].w_rms,
        x_offset: values[option].x_offset,
        lens_transmittance: values[option].lens_transmittance,
        focal_length: values[option].focal_length,
        phi: values[option].phi,
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
    setResultSource(null);
    if (option === 'isotropy') {
      setActiveTab('forward');
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
        c_probe: prev.c_probe || '0.70',
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
      setMediumOption('air');
    }
  };

  const handleLaserOptionChange = (option: LaserOption) => {
    setLaserOption(option);
    const opticalValues = {
      'TOPS 1': { incident_pump: '1.06', incident_probe: '0.85', w_probe_det: '0.971' },
      'TOPS 2': { incident_pump: '1.06', incident_probe: '0.85', w_probe_det: '0.87' },
    };
    if (option === 'TOPS 1') {
      setParams((prev) => ({
        ...prev,
        delay_0: TOPS1_DEFAULTS.delay_0,
        delay_1: TOPS1_DEFAULTS.delay_1,
        delay_2: TOPS1_DEFAULTS.delay_2,
        amplitude_corrected_0: TOPS1_DEFAULTS.amplitude_corrected_0,
        amplitude_corrected_1: TOPS1_DEFAULTS.amplitude_corrected_1,
        amplitude_corrected_2: TOPS1_DEFAULTS.amplitude_corrected_2,
        amplitude_corrected_3: TOPS1_DEFAULTS.amplitude_corrected_3,
        incident_pump: opticalValues['TOPS 1'].incident_pump,
        incident_probe: opticalValues['TOPS 1'].incident_probe,
        w_probe_det: opticalValues['TOPS 1'].w_probe_det,
      }));
    } else {
      setParams((prev) => ({
        ...prev,
        delay_0: TOPS2_DEFAULTS.delay_0,
        delay_1: TOPS2_DEFAULTS.delay_1,
        delay_2: TOPS2_DEFAULTS.delay_2,
        amplitude_corrected_0: TOPS2_DEFAULTS.amplitude_corrected_0,
        amplitude_corrected_1: TOPS2_DEFAULTS.amplitude_corrected_1,
        amplitude_corrected_2: TOPS2_DEFAULTS.amplitude_corrected_2,
        amplitude_corrected_3: TOPS2_DEFAULTS.amplitude_corrected_3,
        incident_pump: opticalValues['TOPS 2'].incident_pump,
        incident_probe: opticalValues['TOPS 2'].incident_probe,
        w_probe_det: opticalValues['TOPS 2'].w_probe_det,
      }));
    }
  };

  const handleClear = () => {
    setParams({
      delay_0: '',
      delay_1: '',
      delay_2: '',
      amplitude_corrected_0: '',
      amplitude_corrected_1: '',
      amplitude_corrected_2: '',
      amplitude_corrected_3: '',
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
      focal_length: '',
      w_probe_det: '',
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
      include_air_deflection: false,
      dndt_up: '',
    });
    setFile(null);
    setLensOption('custom');
    setMediumOption('custom');
    setIsotropyOption('anisotropy');
    setLaserOption('TOPS 1');
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
    setTimeTaken(null);
    const startTime = performance.now();

    const formData = new FormData();
    formData.append('file', file);

    if (isotropyOption === 'transverse_anisotropy') {
      // Transverse anisotropy mode: map shared fields to backend param names with unit conversions
      const transverseParams = {
        delay_0: parseFloat(params.delay_0),
        delay_1: parseFloat(params.delay_1),
        delay_2: parseFloat(params.delay_2),
        amplitude_corrected_0: parseFloat(params.amplitude_corrected_0),
        amplitude_corrected_1: parseFloat(params.amplitude_corrected_1),
        amplitude_corrected_2: parseFloat(params.amplitude_corrected_2),
        amplitude_corrected_3: parseFloat(params.amplitude_corrected_3),
        incident_pump: parseFloat(params.incident_pump) * 1e-3, // mW -> W
        v_sum_fixed: parseFloat(params.v_sum_fixed),
        w_rms: parseFloat(params.w_rms) * 1e-6, // µm -> m
        r_0: parseFloat(params.x_offset) * 1e-6, // µm -> m (x_offset -> r_0)
        lens_transmittance: parseFloat(params.lens_transmittance),
        // det_factor = sqrt(8/pi) * focal_length / w_1_d; mm/mm cancels to dimensionless 1/rad
        detector_gain:
          Math.sqrt(8 / Math.PI) *
          (parseFloat(params.focal_length) / parseFloat(params.w_probe_det)),
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
          setTimeTaken((performance.now() - startTime) / 1000);
          setResult(data);
          setResultSource('analysis');
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

    // det_factor = sqrt(8/pi) * focal_length / w_1_d; mm/mm cancels to dimensionless 1/rad
    const detector_factor =
      Math.sqrt(8 / Math.PI) * (parseFloat(params.focal_length) / parseFloat(params.w_probe_det));
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
      detector_factor: detector_factor.toString(),
      focal_length: undefined,
      w_probe_det: undefined,
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
            include_air_deflection: undefined,
            dndt_up: undefined,
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
        setTimeTaken((performance.now() - startTime) / 1000);
        setResult(data);
        setResultSource('analysis');
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

  // Field definitions for the leaking-correction inputs, varying by laser mode.
  // These values are instrument-specific and shown read-only on the UI;
  // edit them in `laserDefaults.ts`.
  const leakingFields: { field: keyof FDPBDParams; label: string }[] = [
    { field: 'amplitude_corrected_0', label: 'Amplitude Corrected (constant)' },
    { field: 'amplitude_corrected_1', label: 'Amplitude Corrected (1st order)' },
    { field: 'amplitude_corrected_2', label: 'Amplitude Corrected (2nd order)' },
    { field: 'amplitude_corrected_3', label: 'Amplitude Corrected (3rd order)' },
    { field: 'delay_0', label: 'delay (constant)' },
    { field: 'delay_1', label: `delay (1st order) [${fieldUnits.delay_1}]` },
    { field: 'delay_2', label: `delay (2nd order) [${fieldUnits.delay_2}]` },
  ];

  const renderLaserSection = (radioName: string, includeIncidentProbe = true) => {
    const opticalFields = [
      { field: 'incident_pump', label: `Incident Pump [${fieldUnits.incident_pump}]` },
      ...(includeIncidentProbe
        ? [{ field: 'incident_probe', label: `Incident Probe [${fieldUnits.incident_probe}]` }]
        : []),
      { field: 'w_probe_det', label: `Probe Radius at Detector [${fieldUnits.w_probe_det}]` },
    ];
    return (
      <div className="px-4 pb-4">
        <div className="mb-2 flex items-center space-x-4">
          {(['TOPS 1', 'TOPS 2'] as LaserOption[]).map((opt) => (
            <label key={opt} className="flex items-center text-white">
              <input
                type="radio"
                name={radioName}
                value={opt}
                checked={laserOption === opt}
                onChange={() => handleLaserOptionChange(opt)}
                className="mr-2"
                disabled={isProcessing}
              />
              {opt}
            </label>
          ))}
          <span
            className="inline-flex h-4 w-4 flex-none cursor-help items-center justify-center text-gray-300"
            title={`Leaking-correction values below are read-only and instrument-specific. Edit them in: ${LASER_DEFAULTS_PATH}`}
            aria-label="Info"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 16 16"
              width="16"
              height="16"
              fill="currentColor"
              aria-hidden="true"
            >
              <path d="M8 0a8 8 0 1 0 0 16A8 8 0 0 0 8 0Zm0 14.5a6.5 6.5 0 1 1 0-13 6.5 6.5 0 0 1 0 13ZM7.25 6.75h1.5v5h-1.5v-5Zm.75-2.5a1 1 0 1 1 0 2 1 1 0 0 1 0-2Z" />
            </svg>
          </span>
        </div>
        {leakingFields.map((param) => (
          <div key={param.field} className="mb-2 flex flex-col">
            <label className="mb-1 text-sm text-white">{param.label}</label>
            <input
              type="text"
              value={params[param.field] as string}
              readOnly
              tabIndex={-1}
              className="cursor-not-allowed rounded border-2 border-gray-600 bg-gray-900 p-2 text-gray-300 focus:outline-none"
            />
          </div>
        ))}
        {opticalFields.map((param) => (
          <div key={param.field} className="mb-2 flex flex-col">
            <label className="mb-1 text-sm text-white">{param.label}</label>
            <input
              type="number"
              step="any"
              value={params[param.field as keyof FDPBDParams] as string}
              onChange={(e) => handleInputChange(e, param.field as keyof FDPBDParams)}
              className={`rounded border-2 bg-gray-800 p-2 text-white focus:outline-none ${
                isValidDecimal(params[param.field as keyof FDPBDParams] as string)
                  ? 'border-gray-600 focus:border-teal-500'
                  : 'border-red-500'
              }`}
              disabled={isProcessing}
              required
            />
          </div>
        ))}
      </div>
    );
  };

  const anisotropicFitParams = [
    { value: 'sigma_x', label: 'Thermal Conductivity X (σx)' },
    { value: 'sigma_y', label: 'Thermal Conductivity Y (σy)' },
    { value: 'sigma_z', label: 'Thermal Conductivity Z (σz)' },
    { value: 'alphaT_perp', label: 'CTE Perpendicular (αT⊥)' },
    { value: 'alphaT_para', label: 'CTE Parallel (αT∥)' },
  ];
  const transverseFitParams = [
    { value: 'sigma_r', label: 'Thermal Conductivity In-plane (σr)' },
    { value: 'sigma_z', label: 'Thermal Conductivity Through-plane (σz)' },
    { value: 'alphaT_perp', label: 'CTE Perpendicular (αT⊥)' },
    { value: 'alphaT_para', label: 'CTE Parallel (αT∥)' },
  ];
  const currentFitParams =
    isotropyOption === 'anisotropy' ? anisotropicFitParams : transverseFitParams;

  const handleFit = async () => {
    if (!file || !fitParam || !fitBoundsMin || !fitBoundsMax) {
      setStatus('Please fill in all fitting fields');
      return;
    }
    setIsFitting(true);
    setFitProgress(null);
    setFitResult(null);
    setStatus('Fitting...');

    const formData = new FormData();
    formData.append('file', file);

    let endpoint: string;

    if (isotropyOption === 'transverse_anisotropy') {
      const transverseParams = {
        delay_0: parseFloat(params.delay_0),
        delay_1: parseFloat(params.delay_1),
        delay_2: parseFloat(params.delay_2),
        amplitude_corrected_0: parseFloat(params.amplitude_corrected_0),
        amplitude_corrected_1: parseFloat(params.amplitude_corrected_1),
        amplitude_corrected_2: parseFloat(params.amplitude_corrected_2),
        amplitude_corrected_3: parseFloat(params.amplitude_corrected_3),
        incident_pump: parseFloat(params.incident_pump) * 1e-3,
        v_sum_fixed: parseFloat(params.v_sum_fixed),
        w_rms: parseFloat(params.w_rms) * 1e-6,
        r_0: parseFloat(params.x_offset) * 1e-6,
        lens_transmittance: parseFloat(params.lens_transmittance),
        detector_gain:
          Math.sqrt(8 / Math.PI) *
          (parseFloat(params.focal_length) / parseFloat(params.w_probe_det)),
        c_probe: parseFloat(params.c_probe),
        n_al: parseFloat(params.n_al),
        k_al: parseFloat(params.k_al),
        g_int: parseFloat(params.g_int),
        layer1_thickness: parseFloat(params.h_down[0]) * 1e-6,
        layer1_sigma: parseFloat(params.lambda_down[0]),
        layer1_capac: parseFloat(params.c_down[0]) * 1e6,
        layer1_rho: parseFloat(params.rho) * 1e3,
        layer1_alphaT: parseFloat(params.alphaT),
        layer1_C11_0: parseFloat(params.C11_0) * 1e9,
        layer1_C12_0: parseFloat(params.C12_0) * 1e9,
        layer1_C44_0: parseFloat(params.C44_0) * 1e9,
        layer2_sigma_r: parseFloat(params.lambda_down_x_sample),
        layer2_sigma_z: parseFloat(params.lambda_down_z_sample),
        layer2_capac: parseFloat(params.c_down[2]) * 1e6,
        layer2_rho: parseFloat(params.rho_sample) * 1e3,
        layer2_alphaT_perp: parseFloat(params.alphaT_perp),
        layer2_alphaT_para: parseFloat(params.alphaT_para),
        layer2_C11_0: parseFloat(params.C11_0_sample) * 1e9,
        layer2_C12_0: parseFloat(params.C12_0_sample) * 1e9,
        layer2_C13_0: parseFloat(params.C13_0_sample) * 1e9,
        layer2_C33_0: parseFloat(params.C33_0_sample) * 1e9,
        layer2_C44_0: parseFloat(params.C44_0_sample) * 1e9,
        layer3_sigma: parseFloat(params.lambda_up),
        layer3_capac: parseFloat(params.c_up),
        fit_parameter: fitParam,
        fit_bounds_min: parseFloat(fitBoundsMin),
        fit_bounds_max: parseFloat(fitBoundsMax),
        fit_maxiter: parseInt(fitMaxIter) || 20,
        fit_popsize: parseInt(fitPopSize) || 8,
        fit_tol: parseFloat(fitTol) || 1e-3,
      };
      formData.append('params', JSON.stringify(transverseParams));
      endpoint = `${API_BASE}/fdpbd/fit_transverse`;
    } else {
      const detector_factor =
        Math.sqrt(8 / Math.PI) * (parseFloat(params.focal_length) / parseFloat(params.w_probe_det));
      const anisotropicParams = {
        ...params,
        detector_factor: detector_factor.toString(),
        focal_length: undefined,
        w_probe_det: undefined,
        w_rms: (parseFloat(params.w_rms) * 1e-6).toString(),
        x_offset: (parseFloat(params.x_offset) * 1e-6).toString(),
        incident_probe: (parseFloat(params.incident_probe) * 1e-3).toString(),
        incident_pump: (parseFloat(params.incident_pump) * 1e-3).toString(),
        c_down: params.c_down.map((c) => (parseFloat(c) * 1e6).toString()),
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
        eta_up: undefined,
        h_up: undefined,
        lambda_down: [params.lambda_down[0]],
        h_down: [(parseFloat(params.h_down[0]) * 1e-6).toString()],
        niu: undefined,
        alpha_t: undefined,
        fit_parameter: fitParam,
        fit_bounds_min: parseFloat(fitBoundsMin),
        fit_bounds_max: parseFloat(fitBoundsMax),
        fit_maxiter: parseInt(fitMaxIter) || 20,
        fit_popsize: parseInt(fitPopSize) || 8,
        fit_tol: parseFloat(fitTol) || 1e-3,
      };
      formData.append('params', JSON.stringify(anisotropicParams));
      endpoint = `${API_BASE}/fdpbd/fit_anisotropy`;
    }

    try {
      const response = await fetch(endpoint, { method: 'POST', body: formData });
      if (!response.ok || !response.body) {
        const errorData = await response.json().catch(() => ({}));
        setStatus(`Error: ${errorData.detail || 'Fitting failed'}`);
        setIsFitting(false);
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const rawLine of lines) {
          const line = rawLine.trim();
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              console.log('[fit-sse]', data.type, data);
              if (data.type === 'progress') {
                setFitProgress(data);
                setStatus(
                  `Fitting... Gen ${data.generation} — Best: ${data.best_value.toExponential(4)} — ${data.elapsed}s`
                );
              } else if (data.type === 'result') {
                setFitResult(data);
                setResult(data);
                setResultSource('fit');
                setTimeTaken(data.elapsed);
                setStatus('Fitting completed');
              } else if (data.type === 'error') {
                setStatus(`Error: ${data.message}`);
              }
            } catch {
              // skip malformed JSON
            }
          }
        }
      }
    } catch (error) {
      console.error('Fit error:', error);
      setStatus('Error occurred during fitting');
    } finally {
      setIsFitting(false);
    }
  };

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-gray-900">
      {/* Header */}
      <header className="flex items-center justify-between bg-gray-800 p-4">
        <h1 className="text-xl font-semibold text-white">Analysis</h1>
        <Link href="/" className="text-white hover:text-teal-400">
          Back to Dashboard
        </Link>
      </header>

      {/* Main Layout */}
      <div className="flex min-h-0 flex-1 space-x-4 p-4">
        {/* Left Panel: Input Form */}
        <div className="flex w-1/3 flex-col">
          {/* Shared: File Upload + Mode Selection */}
          <div className="rounded-t-lg bg-gray-800 px-4 pt-4">
            <div className="mb-3">
              <h3 className="text-md mb-2 font-semibold text-white">Data File (.txt)</h3>
              <input
                type="file"
                accept=".txt"
                onChange={handleFileChange}
                className="w-full rounded bg-gray-700 p-2 text-white"
                disabled={isProcessing}
              />
            </div>
            <div className="mb-3 rounded-lg bg-gray-700 p-3">
              <h4 className="mb-2 text-sm font-semibold text-white">Analysis Mode</h4>
              <div className="mb-1 flex flex-wrap gap-4">
                {[
                  { value: 'isotropy', label: 'Isotropic' },
                  { value: 'anisotropy', label: 'Anisotropic' },
                  { value: 'transverse_anisotropy', label: 'Transversely Isotropic' },
                ].map((opt) => (
                  <label key={opt.value} className="flex items-center text-sm text-white">
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
            {/* Tab Bar */}
            <div className="flex border-b border-gray-600">
              <button
                onClick={() => setActiveTab('forward')}
                className={`flex-1 py-2 text-sm font-medium transition-colors ${
                  activeTab === 'forward'
                    ? 'border-b-2 border-teal-500 text-teal-400'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                Forward Model
              </button>
              {isotropyOption !== 'isotropy' && (
                <button
                  onClick={() => setActiveTab('fitting')}
                  className={`flex-1 py-2 text-sm font-medium transition-colors ${
                    activeTab === 'fitting'
                      ? 'border-b-2 border-orange-500 text-orange-400'
                      : 'text-gray-400 hover:text-gray-200'
                  }`}
                >
                  DE Fitting
                </button>
              )}
            </div>
          </div>

          {/* Scrollable Content Area */}
          <div className="flex-1 overflow-y-auto bg-gray-800 px-4 pb-2">
            {/* Forward Model Tab */}
            {activeTab === 'forward' && (
              <div className="pt-4">
                {/* Isotropy/Anisotropy form fields */}
                {isotropyOption !== 'transverse_anisotropy' && (
                  <>
                    {/* Experimental Inputs */}
                    <div className="mb-6">
                      <h3 className="text-md mb-2 font-semibold text-white">Experimental Inputs</h3>
                      {/* Laser */}
                      <div className="mb-4 rounded-lg bg-gray-700">
                        <button
                          onClick={() => toggleSection('laser')}
                          className="flex w-full items-center justify-between p-4 text-left"
                        >
                          <h4 className="text-sm font-semibold text-white">Laser</h4>
                          <span
                            className={`text-gray-400 transition-transform ${collapsedSections.has('laser') ? '' : 'rotate-180'}`}
                          >
                            &#9650;
                          </span>
                        </button>
                        {!collapsedSections.has('laser') && renderLaserSection('laser', true)}
                      </div>
                      {/* Lens Magnification */}
                      <div className="rounded-lg bg-gray-700">
                        <button
                          onClick={() => toggleSection('lens')}
                          className="flex w-full items-center justify-between p-4 text-left"
                        >
                          <h4 className="text-sm font-semibold text-white">Lens Magnification</h4>
                          <span
                            className={`text-gray-400 transition-transform ${collapsedSections.has('lens') ? '' : 'rotate-180'}`}
                          >
                            &#9650;
                          </span>
                        </button>
                        {!collapsedSections.has('lens') && (
                          <div className="px-4 pb-4">
                            <div className="mb-2 flex space-x-4">
                              {['2x', '5x', '10x', '20x', 'custom'].map((opt) => (
                                <label key={opt} className="flex items-center text-white">
                                  <input
                                    type="radio"
                                    name="lens"
                                    value={opt}
                                    checked={lensOption === opt}
                                    onChange={() =>
                                      handleLensOptionChange(opt as '2x' | '5x' | '10x' | '20x' | 'custom')
                                    }
                                    className="mr-2"
                                    disabled={isProcessing}
                                  />
                                  {opt}
                                </label>
                              ))}
                            </div>
                            {[
                              { field: 'w_rms', label: `w rms [${fieldUnits.w_rms}]` },
                              {
                                field: 'x_offset',
                                label: `X Offset [${fieldUnits.x_offset}]`,
                              },
                              {
                                field: 'lens_transmittance',
                                label: `Lens Transmittance ${
                                  fieldUnits.lens_transmittance
                                    ? `[${fieldUnits.lens_transmittance}]`
                                    : ''
                                }`,
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
                                  value={params[param.field as keyof FDPBDParams] as string}
                                  onChange={(e) =>
                                    handleInputChange(e, param.field as keyof FDPBDParams)
                                  }
                                  className={`rounded border-2 bg-gray-800 p-2 text-white focus:outline-none ${
                                    isValidDecimal(
                                      params[param.field as keyof FDPBDParams] as string
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
                        )}
                      </div>
                    </div>

                    {/* Sample Inputs */}
                    <div className="mb-6">
                      <h3 className="text-md mb-2 font-semibold text-white">Sample Inputs</h3>
                      {/* Medium */}
                      <div className="mb-4 rounded-lg bg-gray-700">
                        <button
                          onClick={() => toggleSection('medium')}
                          className="flex w-full items-center justify-between p-4 text-left"
                        >
                          <h4 className="text-sm font-semibold text-white">Medium</h4>
                          <span
                            className={`text-gray-400 transition-transform ${collapsedSections.has('medium') ? '' : 'rotate-180'}`}
                          >
                            &#9650;
                          </span>
                        </button>
                        {!collapsedSections.has('medium') && (
                          <div className="px-4 pb-4">
                            <div className="mb-2 flex space-x-4">
                              {['air', 'custom'].map((opt) => (
                                <label key={opt} className="flex items-center text-white">
                                  <input
                                    type="radio"
                                    name="medium"
                                    value={opt}
                                    checked={mediumOption === opt}
                                    onChange={() =>
                                      handleMediumOptionChange(opt as 'air' | 'custom')
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
                                  ]
                                : []),
                            ].map((param) => (
                              <div key={param.field} className="mb-2 flex flex-col">
                                <label className="mb-1 text-sm text-white">{param.label}</label>
                                <input
                                  type="number"
                                  step="any"
                                  value={params[param.field as keyof FDPBDParams] as string}
                                  onChange={(e) =>
                                    handleInputChange(e, param.field as keyof FDPBDParams)
                                  }
                                  className={`rounded border-2 bg-gray-800 p-2 text-white focus:outline-none ${
                                    isValidDecimal(
                                      params[param.field as keyof FDPBDParams] as string
                                    )
                                      ? 'border-gray-600 focus:border-teal-500'
                                      : 'border-red-500'
                                  }`}
                                  disabled={isProcessing}
                                  required
                                />
                              </div>
                            ))}
                            {isotropyOption === 'isotropy' && (
                              <>
                                <div className="mb-2 mt-3 flex items-center">
                                  <input
                                    type="checkbox"
                                    id="include_air_deflection"
                                    checked={params.include_air_deflection}
                                    onChange={(e) =>
                                      setParams((prev) => ({
                                        ...prev,
                                        include_air_deflection: e.target.checked,
                                      }))
                                    }
                                    className="mr-2 accent-teal-500"
                                    disabled={isProcessing}
                                  />
                                  <label
                                    htmlFor="include_air_deflection"
                                    className="text-sm text-white"
                                  >
                                    Include beam deflection
                                  </label>
                                </div>
                                {params.include_air_deflection && (
                                  <div className="mb-2 flex flex-col">
                                    <label className="mb-1 text-sm text-white">dn/dT [1/K]</label>
                                    <input
                                      type="number"
                                      step="any"
                                      value={params.dndt_up}
                                      onChange={(e) =>
                                        handleInputChange(e, 'dndt_up' as keyof FDPBDParams)
                                      }
                                      className={`rounded border-2 bg-gray-800 p-2 text-white focus:outline-none ${
                                        isValidDecimal(params.dndt_up)
                                          ? 'border-gray-600 focus:border-teal-500'
                                          : 'border-red-500'
                                      }`}
                                      disabled={isProcessing}
                                      required
                                    />
                                  </div>
                                )}
                              </>
                            )}
                          </div>
                        )}
                      </div>
                      {/* Transducer Layer */}
                      <div className="mb-4 rounded-lg bg-gray-700">
                        <button
                          onClick={() => toggleSection('transducer')}
                          className="flex w-full items-center justify-between p-4 text-left"
                        >
                          <h4 className="text-sm font-semibold text-white">Transducer Layer</h4>
                          <span
                            className={`text-gray-400 transition-transform ${collapsedSections.has('transducer') ? '' : 'rotate-180'}`}
                          >
                            &#9650;
                          </span>
                        </button>
                        {!collapsedSections.has('transducer') && (
                          <div className="px-4 pb-4">
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
                                      ? (params[param.field as keyof FDPBDParams] as string[])[
                                          param.index
                                        ]
                                      : (params[param.field as keyof FDPBDParams] as string)
                                  }
                                  onChange={(e) =>
                                    handleInputChange(
                                      e,
                                      param.field as keyof FDPBDParams,
                                      param.index
                                    )
                                  }
                                  className={`rounded border-2 bg-gray-800 p-2 text-white focus:outline-none ${
                                    isValidDecimal(
                                      param.index !== undefined
                                        ? (params[param.field as keyof FDPBDParams] as string[])[
                                            param.index
                                          ]
                                        : (params[param.field as keyof FDPBDParams] as string)
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
                        )}
                      </div>
                      {/* Interface Layer */}
                      {isotropyOption === 'isotropy' && (
                        <div className="mb-4 rounded-lg bg-gray-700">
                          <button
                            onClick={() => toggleSection('interface')}
                            className="flex w-full items-center justify-between p-4 text-left"
                          >
                            <h4 className="text-sm font-semibold text-white">Interface Layer</h4>
                            <span
                              className={`text-gray-400 transition-transform ${collapsedSections.has('interface') ? '' : 'rotate-180'}`}
                            >
                              &#9650;
                            </span>
                          </button>
                          {!collapsedSections.has('interface') && (
                            <div className="px-4 pb-4">
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
                                <div
                                  key={`${param.field}${param.index}`}
                                  className="mb-2 flex flex-col"
                                >
                                  <label className="mb-1 text-sm text-white">{param.label}</label>
                                  <input
                                    type="number"
                                    step="any"
                                    value={
                                      (params[param.field as keyof FDPBDParams] as string[])[
                                        param.index
                                      ]
                                    }
                                    onChange={(e) =>
                                      handleInputChange(
                                        e,
                                        param.field as keyof FDPBDParams,
                                        param.index
                                      )
                                    }
                                    className={`rounded border-2 bg-gray-800 p-2 text-white focus:outline-none ${
                                      isValidDecimal(
                                        (params[param.field as keyof FDPBDParams] as string[])[
                                          param.index
                                        ]
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
                          )}
                        </div>
                      )}
                      {/* Sample Layer */}
                      <div className="mb-4 rounded-lg bg-gray-700">
                        <button
                          onClick={() => toggleSection('sample')}
                          className="flex w-full items-center justify-between p-4 text-left"
                        >
                          <h4 className="text-sm font-semibold text-white">Sample Layer</h4>
                          <span
                            className={`text-gray-400 transition-transform ${collapsedSections.has('sample') ? '' : 'rotate-180'}`}
                          >
                            &#9650;
                          </span>
                        </button>
                        {!collapsedSections.has('sample') && (
                          <div className="px-4 pb-4">
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
                                      label: `Poisson Ratio ${fieldUnits.niu ? `[${fieldUnits.niu}]` : ''}`,
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
                                      ? (params[param.field as keyof FDPBDParams] as string[])[
                                          param.index
                                        ]
                                      : (params[param.field as keyof FDPBDParams] as string)
                                  }
                                  onChange={(e) =>
                                    handleInputChange(
                                      e,
                                      param.field as keyof FDPBDParams,
                                      param.index
                                    )
                                  }
                                  className={`rounded border-2 bg-gray-800 p-2 text-white focus:outline-none ${
                                    isValidDecimal(
                                      param.index !== undefined
                                        ? (params[param.field as keyof FDPBDParams] as string[])[
                                            param.index
                                          ]
                                        : (params[param.field as keyof FDPBDParams] as string)
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
                        )}
                      </div>
                    </div>
                  </>
                )}

                {/* Transverse Anisotropy form fields */}
                {isotropyOption === 'transverse_anisotropy' && (
                  <>
                    <div className="mb-6">
                      <h3 className="text-md mb-2 font-semibold text-white">Experimental Inputs</h3>
                      {/* Laser */}
                      <div className="mb-4 rounded-lg bg-gray-700">
                        <button
                          onClick={() => toggleSection('t_laser')}
                          className="flex w-full items-center justify-between p-4 text-left"
                        >
                          <h4 className="text-sm font-semibold text-white">Laser</h4>
                          <span
                            className={`text-gray-400 transition-transform ${collapsedSections.has('t_laser') ? '' : 'rotate-180'}`}
                          >
                            &#9650;
                          </span>
                        </button>
                        {!collapsedSections.has('t_laser') &&
                          renderLaserSection('laser_transverse', false)}
                      </div>

                      {/* Lens Magnification */}
                      <div className="mb-4 rounded-lg bg-gray-700">
                        <button
                          onClick={() => toggleSection('t_lens')}
                          className="flex w-full items-center justify-between p-4 text-left"
                        >
                          <h4 className="text-sm font-semibold text-white">Lens Magnification</h4>
                          <span
                            className={`text-gray-400 transition-transform ${collapsedSections.has('t_lens') ? '' : 'rotate-180'}`}
                          >
                            &#9650;
                          </span>
                        </button>
                        {!collapsedSections.has('t_lens') && (
                          <div className="px-4 pb-4">
                            <div className="mb-2 flex space-x-4">
                              {['2x', '5x', '10x', '20x', 'custom'].map((opt) => (
                                <label key={opt} className="flex items-center text-white">
                                  <input
                                    type="radio"
                                    name="lens_transverse"
                                    value={opt}
                                    checked={lensOption === opt}
                                    onChange={() =>
                                      handleLensOptionChange(opt as '2x' | '5x' | '10x' | '20x' | 'custom')
                                    }
                                    className="mr-2"
                                    disabled={isProcessing}
                                  />
                                  {opt}
                                </label>
                              ))}
                            </div>
                            {[
                              { field: 'w_rms', label: `w rms [${fieldUnits.w_rms}]` },
                              { field: 'x_offset', label: `X Offset [${fieldUnits.x_offset}]` },
                              { field: 'lens_transmittance', label: 'Lens Transmittance' },
                              {
                                field: 'v_sum_fixed',
                                label: `V Sum Fixed [${fieldUnits.v_sum_fixed}]`,
                              },
                              { field: 'c_probe', label: 'C Probe' },
                            ].map((param) => (
                              <div key={param.field} className="mb-2 flex flex-col">
                                <label className="mb-1 text-sm text-white">{param.label}</label>
                                <input
                                  type="number"
                                  step="any"
                                  value={params[param.field as keyof FDPBDParams] as string}
                                  onChange={(e) =>
                                    handleInputChange(e, param.field as keyof FDPBDParams)
                                  }
                                  className={`rounded border-2 bg-gray-800 p-2 text-white focus:outline-none ${
                                    isValidDecimal(
                                      params[param.field as keyof FDPBDParams] as string
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
                        )}
                      </div>
                    </div>

                    {/* Sample Inputs */}
                    <div className="mb-6">
                      <h3 className="text-md mb-2 font-semibold text-white">Sample Inputs</h3>

                      {/* Medium (Air / Layer 3) */}
                      <div className="mb-4 rounded-lg bg-gray-700">
                        <button
                          onClick={() => toggleSection('t_medium')}
                          className="flex w-full items-center justify-between p-4 text-left"
                        >
                          <h4 className="text-sm font-semibold text-white">Medium</h4>
                          <span
                            className={`text-gray-400 transition-transform ${collapsedSections.has('t_medium') ? '' : 'rotate-180'}`}
                          >
                            &#9650;
                          </span>
                        </button>
                        {!collapsedSections.has('t_medium') && (
                          <div className="px-4 pb-4">
                            <div className="mb-2 flex space-x-4">
                              {['air', 'custom'].map((opt) => (
                                <label key={opt} className="flex items-center text-white">
                                  <input
                                    type="radio"
                                    name="medium_transverse"
                                    value={opt}
                                    checked={mediumOption === opt}
                                    onChange={() =>
                                      handleMediumOptionChange(opt as 'air' | 'custom')
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
                                  value={params[param.field as keyof FDPBDParams] as string}
                                  onChange={(e) =>
                                    handleInputChange(e, param.field as keyof FDPBDParams)
                                  }
                                  className={`rounded border-2 bg-gray-800 p-2 text-white focus:outline-none ${
                                    isValidDecimal(
                                      params[param.field as keyof FDPBDParams] as string
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
                        )}
                      </div>

                      {/* Transducer Layer (Al Film / Layer 1) */}
                      <div className="mb-4 rounded-lg bg-gray-700">
                        <button
                          onClick={() => toggleSection('t_transducer')}
                          className="flex w-full items-center justify-between p-4 text-left"
                        >
                          <h4 className="text-sm font-semibold text-white">
                            Transducer Layer (Al Film)
                          </h4>
                          <span
                            className={`text-gray-400 transition-transform ${collapsedSections.has('t_transducer') ? '' : 'rotate-180'}`}
                          >
                            &#9650;
                          </span>
                        </button>
                        {!collapsedSections.has('t_transducer') && (
                          <div className="px-4 pb-4">
                            {[
                              {
                                field: 'lambda_down',
                                index: 0,
                                label: `Thermal Conductivity [${fieldUnits.lambda_down}]`,
                              },
                              {
                                field: 'c_down',
                                index: 0,
                                label: `Heat Capacity [${fieldUnits.c_down}]`,
                              },
                              {
                                field: 'h_down',
                                index: 0,
                                label: `Thickness [${fieldUnits.h_down}]`,
                              },
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
                                      ? (params[param.field as keyof FDPBDParams] as string[])[
                                          param.index
                                        ]
                                      : (params[param.field as keyof FDPBDParams] as string)
                                  }
                                  onChange={(e) =>
                                    handleInputChange(
                                      e,
                                      param.field as keyof FDPBDParams,
                                      param.index
                                    )
                                  }
                                  className={`rounded border-2 bg-gray-800 p-2 text-white focus:outline-none ${
                                    isValidDecimal(
                                      param.index !== undefined
                                        ? (params[param.field as keyof FDPBDParams] as string[])[
                                            param.index
                                          ]
                                        : (params[param.field as keyof FDPBDParams] as string)
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
                        )}
                      </div>

                      {/* Sample Layer (Bulk / Layer 2) */}
                      <div className="mb-4 rounded-lg bg-gray-700">
                        <button
                          onClick={() => toggleSection('t_sample')}
                          className="flex w-full items-center justify-between p-4 text-left"
                        >
                          <h4 className="text-sm font-semibold text-white">Sample Layer (Bulk)</h4>
                          <span
                            className={`text-gray-400 transition-transform ${collapsedSections.has('t_sample') ? '' : 'rotate-180'}`}
                          >
                            &#9650;
                          </span>
                        </button>
                        {!collapsedSections.has('t_sample') && (
                          <div className="px-4 pb-4">
                            {[
                              {
                                field: 'lambda_down_x_sample',
                                label: `In-plane Conductivity [${fieldUnits.lambda_down_x_sample}]`,
                              },
                              {
                                field: 'lambda_down_z_sample',
                                label: `Through-plane Conductivity [${fieldUnits.lambda_down_z_sample}]`,
                              },
                              {
                                field: 'c_down',
                                index: 2,
                                label: `Heat Capacity [${fieldUnits.c_down}]`,
                              },
                              { field: 'rho_sample', label: `Density [${fieldUnits.rho_sample}]` },
                              {
                                field: 'alphaT_perp',
                                label: `CTE In-plane [${fieldUnits.alphaT_perp}]`,
                              },
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
                                      ? (params[param.field as keyof FDPBDParams] as string[])[
                                          param.index
                                        ]
                                      : (params[param.field as keyof FDPBDParams] as string)
                                  }
                                  onChange={(e) =>
                                    handleInputChange(
                                      e,
                                      param.field as keyof FDPBDParams,
                                      param.index
                                    )
                                  }
                                  className={`rounded border-2 bg-gray-800 p-2 text-white focus:outline-none ${
                                    isValidDecimal(
                                      param.index !== undefined
                                        ? (params[param.field as keyof FDPBDParams] as string[])[
                                            param.index
                                          ]
                                        : (params[param.field as keyof FDPBDParams] as string)
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
                        )}
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}

            {/* DE Fitting Tab */}
            {activeTab === 'fitting' && isotropyOption !== 'isotropy' && (
              <div className="pt-4">
                <div className="mb-2 flex flex-col">
                  <label className="mb-1 text-sm text-gray-300">Parameter to Fit</label>
                  <select
                    value={fitParam}
                    onChange={(e) => setFitParam(e.target.value)}
                    className="rounded bg-gray-700 px-2 py-1 text-sm text-white"
                    disabled={isFitting}
                  >
                    <option value="">Select parameter...</option>
                    {currentFitParams.map((p) => (
                      <option key={p.value} value={p.value}>
                        {p.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="mb-2 flex space-x-2">
                  <div className="flex-1">
                    <label className="mb-1 block text-sm text-gray-300">Min Bound</label>
                    <input
                      type="number"
                      step="any"
                      value={fitBoundsMin}
                      onChange={(e) => setFitBoundsMin(e.target.value)}
                      className="w-full rounded bg-gray-700 px-2 py-1 text-sm text-white"
                      disabled={isFitting}
                    />
                  </div>
                  <div className="flex-1">
                    <label className="mb-1 block text-sm text-gray-300">Max Bound</label>
                    <input
                      type="number"
                      step="any"
                      value={fitBoundsMax}
                      onChange={(e) => setFitBoundsMax(e.target.value)}
                      className="w-full rounded bg-gray-700 px-2 py-1 text-sm text-white"
                      disabled={isFitting}
                    />
                  </div>
                </div>
                <div className="mb-3 flex space-x-2">
                  <div className="flex-1">
                    <label className="mb-1 block text-sm text-gray-300">Max Iter</label>
                    <input
                      type="number"
                      value={fitMaxIter}
                      onChange={(e) => setFitMaxIter(e.target.value)}
                      className="w-full rounded bg-gray-700 px-2 py-1 text-sm text-white"
                      disabled={isFitting}
                    />
                  </div>
                  <div className="flex-1">
                    <label className="mb-1 block text-sm text-gray-300">Pop Size</label>
                    <input
                      type="number"
                      value={fitPopSize}
                      onChange={(e) => setFitPopSize(e.target.value)}
                      className="w-full rounded bg-gray-700 px-2 py-1 text-sm text-white"
                      disabled={isFitting}
                    />
                  </div>
                  <div className="flex-1">
                    <label className="mb-1 block text-sm text-gray-300">Tolerance</label>
                    <input
                      type="text"
                      value={fitTol}
                      onChange={(e) => setFitTol(e.target.value)}
                      className="w-full rounded bg-gray-700 px-2 py-1 text-sm text-white"
                      disabled={isFitting}
                    />
                  </div>
                </div>
                {fitProgress && isFitting && (
                  <div className="mb-2 rounded bg-gray-700 p-2 text-xs text-gray-300">
                    <p>
                      Generation {fitProgress.generation} — Best:{' '}
                      {fitProgress.best_value.toExponential(4)} — Convergence:{' '}
                      {fitProgress.convergence.toExponential(2)} — {fitProgress.elapsed}s
                    </p>
                  </div>
                )}
                {fitResult && (
                  <div className="mb-2 rounded bg-green-900/30 p-2 text-sm text-green-300">
                    <p>
                      Fitted <strong>{fitResult.fit_param}</strong> ={' '}
                      {fitResult.best_value.toExponential(4)}
                    </p>
                    <p className="text-xs text-gray-400">
                      Cost: {fitResult.cost.toExponential(3)} — {fitResult.generations} generations
                      — {fitResult.elapsed}s
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Sticky Action Bar */}
          <div className="rounded-b-lg border-t border-gray-600 bg-gray-800 px-4 py-3">
            {activeTab === 'forward' ? (
              <>
                <div className="flex space-x-4">
                  <button
                    onClick={handleSubmit}
                    disabled={isProcessing || isFitting || !isFormValid()}
                    className={`flex-1 rounded py-2 text-white ${
                      isProcessing || isFitting || !isFormValid()
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
              </>
            ) : (
              <button
                onClick={handleFit}
                disabled={
                  isFitting || isProcessing || !file || !fitParam || !fitBoundsMin || !fitBoundsMax
                }
                className={`w-full rounded py-2 text-sm text-white ${
                  isFitting || isProcessing || !file || !fitParam || !fitBoundsMin || !fitBoundsMax
                    ? 'cursor-not-allowed bg-gray-600'
                    : 'bg-orange-500 hover:bg-orange-600'
                }`}
              >
                {isFitting ? 'Fitting...' : 'Run Fit'}
              </button>
            )}
            {status && status.includes('Error') && (
              <p className="mt-2 text-sm text-red-400">{status}</p>
            )}
          </div>
        </div>

        {/* Right Panel: Results and Graphs */}
        <div className="flex w-2/3 flex-col space-y-4 overflow-y-auto">
          {result && (
            <>
              <div className="rounded-lg bg-gray-800 p-4 shadow-md">
                <div className="mb-4 flex items-center gap-3">
                  <h2 className="text-lg font-semibold text-white">Results</h2>
                  {resultSource && (
                    <span
                      className={`rounded-full px-3 py-0.5 text-xs font-medium ${
                        resultSource === 'fit'
                          ? 'bg-orange-500/20 text-orange-300 ring-1 ring-orange-500/40'
                          : 'bg-teal-500/20 text-teal-300 ring-1 ring-teal-500/40'
                      }`}
                    >
                      {resultSource === 'fit' ? 'DE Fit' : 'Forward Model'}
                    </span>
                  )}
                </div>
                {resultSource === 'fit' && fitResult && (
                  <div className="mb-3 rounded border border-orange-500/30 bg-orange-500/10 p-3">
                    <p className="text-sm font-medium text-orange-300">
                      Fitted <strong>{fitResult.fit_param}</strong> ={' '}
                      {fitResult.best_value.toExponential(4)}
                    </p>
                    <p className="mt-1 text-xs text-gray-400">
                      Cost: {fitResult.cost.toExponential(3)} | {fitResult.generations} generations
                      | {fitResult.elapsed}s
                    </p>
                  </div>
                )}
                {timeTaken !== null && (
                  <p className="mb-2 text-sm text-gray-400">Completed in {timeTaken.toFixed(2)}s</p>
                )}
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
              <div
                className={`rounded-lg bg-gray-800 p-4 shadow-md ${
                  resultSource === 'fit'
                    ? 'border border-orange-500/30'
                    : resultSource === 'analysis'
                      ? 'border border-teal-500/30'
                      : ''
                }`}
              >
                <div className="mb-4 flex items-center gap-3">
                  <h2 className="text-lg font-semibold text-white">Graphs</h2>
                  {resultSource === 'fit' && (
                    <span className="text-xs text-orange-400">Showing fitted model curves</span>
                  )}
                  <div className="ml-auto flex items-center gap-2">
                    <span className="text-xs text-gray-400">Export format</span>
                    <select
                      value={plotExportFormat}
                      onChange={(e) =>
                        setPlotExportFormat(e.target.value as typeof plotExportFormat)
                      }
                      className="rounded bg-gray-700 px-2 py-1 text-xs text-white"
                    >
                      {(['svg', 'png', 'jpeg', 'webp'] as const).map((fmt) => (
                        <option key={fmt} value={fmt}>
                          {fmt.toUpperCase()}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="flex flex-wrap gap-4">
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
                            line: { color: 'black', dash: 'dash' },
                          },
                          {
                            x: (result as FDPBDResult).plot_data.freq_fit,
                            y: (result as FDPBDResult).plot_data.v_corr_out_fit,
                            type: 'scatter',
                            mode: 'markers',
                            name: 'Out-of-phase (data)',
                            marker: { color: 'black' },
                            line: { color: 'black', dash: 'dash' },
                          },
                          {
                            x: (result as FDPBDResult).plot_data.freq_fit,
                            y: (result as FDPBDResult).plot_data.delta_in,
                            type: 'scatter',
                            mode: 'lines',
                            name: 'In-phase (model)',
                            marker: { color: 'blue' },
                            line: { color: 'blue', dash: 'dash' },
                          },
                          {
                            x: (result as FDPBDResult).plot_data.freq_fit,
                            y: (result as FDPBDResult).plot_data.delta_out,
                            type: 'scatter',
                            mode: 'lines',
                            name: 'Out-of-phase (model)',
                            marker: { color: 'red' },
                            line: { color: 'red', dash: 'dash' },
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
                          width: 550,
                          height: 400,
                          margin: { l: 60, r: 30, t: 40, b: 50 },
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
                        config={{ toImageButtonOptions: { format: plotExportFormat } }}
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
                            line: { color: 'black', dash: 'dash' },
                          },
                          {
                            x: (result as FDPBDResult).plot_data.freq_fit,
                            y: (result as FDPBDResult).plot_data.delta_ratio,
                            type: 'scatter',
                            mode: 'lines',
                            name: 'Ratio (model)',
                            marker: { color: 'blue' },
                            line: { color: 'blue', dash: 'dash' },
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
                          width: 550,
                          height: 400,
                          margin: { l: 60, r: 30, t: 40, b: 50 },
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
                        config={{ toImageButtonOptions: { format: plotExportFormat } }}
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
                            line: { color: 'black', dash: 'dash' },
                          },
                          {
                            x: (result as AnisotropicFDPBDResult).plot_data.exp_freqs,
                            y: (result as AnisotropicFDPBDResult).plot_data.out_exp,
                            type: 'scatter',
                            mode: 'markers',
                            name: 'Out-of-phase (data)',
                            marker: { color: 'black' },
                            line: { color: 'black', dash: 'dash' },
                          },
                          {
                            x: (result as AnisotropicFDPBDResult).plot_data.model_freqs,
                            y: (result as AnisotropicFDPBDResult).plot_data.in_model,
                            type: 'scatter',
                            mode: 'lines',
                            name: 'In-phase (model)',
                            marker: { color: 'blue' },
                            line: { color: 'blue', dash: 'dash' },
                          },
                          {
                            x: (result as AnisotropicFDPBDResult).plot_data.model_freqs,
                            y: (result as AnisotropicFDPBDResult).plot_data.out_model,
                            type: 'scatter',
                            mode: 'lines',
                            name: 'Out-of-phase (model)',
                            marker: { color: 'red' },
                            line: { color: 'red', dash: 'dash' },
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
                          width: 550,
                          height: 400,
                          margin: { l: 60, r: 30, t: 40, b: 50 },
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
                        config={{ toImageButtonOptions: { format: plotExportFormat } }}
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
                            line: { color: 'black', dash: 'dash' },
                          },
                          {
                            x: (result as AnisotropicFDPBDResult).plot_data.model_freqs,
                            y: (result as AnisotropicFDPBDResult).plot_data.ratio_model,
                            type: 'scatter',
                            mode: 'lines',
                            name: 'Ratio (model)',
                            marker: { color: 'blue' },
                            line: { color: 'blue', dash: 'dash' },
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
                          width: 550,
                          height: 400,
                          margin: { l: 60, r: 30, t: 40, b: 50 },
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
                        config={{ toImageButtonOptions: { format: plotExportFormat } }}
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
                            line: { color: 'red', dash: 'dash' },
                          },
                          {
                            x: (result as TransverseIsotropicResult).plot_data.exp_freqs,
                            y: (result as TransverseIsotropicResult).plot_data.out_exp,
                            type: 'scatter',
                            mode: 'markers',
                            name: 'Out-of-phase (data)',
                            marker: { color: 'red', symbol: 'x' },
                            line: { color: 'red', dash: 'dash' },
                          },
                          {
                            x: (result as TransverseIsotropicResult).plot_data.model_freqs,
                            y: (result as TransverseIsotropicResult).plot_data.in_model,
                            type: 'scatter',
                            mode: 'lines',
                            name: 'In-phase (model)',
                            line: { color: 'black', dash: 'dash' },
                            marker: { color: 'black' },
                          },
                          {
                            x: (result as TransverseIsotropicResult).plot_data.model_freqs,
                            y: (result as TransverseIsotropicResult).plot_data.out_model,
                            type: 'scatter',
                            mode: 'lines',
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
                          width: 550,
                          height: 400,
                          margin: { l: 60, r: 30, t: 40, b: 50 },
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
                        config={{ toImageButtonOptions: { format: plotExportFormat } }}
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
                            line: { color: 'red', dash: 'dash' },
                          },
                          {
                            x: (result as TransverseIsotropicResult).plot_data.model_freqs,
                            y: (result as TransverseIsotropicResult).plot_data.ratio_model,
                            type: 'scatter',
                            mode: 'lines',
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
                          width: 550,
                          height: 400,
                          margin: { l: 60, r: 30, t: 40, b: 50 },
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
                        config={{ toImageButtonOptions: { format: plotExportFormat } }}
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
