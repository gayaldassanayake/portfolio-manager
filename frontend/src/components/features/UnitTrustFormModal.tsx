import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Modal, ModalFooter, Button, Input, Select, Textarea } from '../ui';
import { ProviderBadge } from '../ui/ProviderBadge';
import { useCreateUnitTrust, useUpdateUnitTrust } from '../../api/hooks';
import type { UnitTrust, UnitTrustCreate, UnitTrustUpdate, Provider } from '../../types';
import styles from './UnitTrustFormModal.module.css';

interface UnitTrustFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  unitTrust?: UnitTrust; // If provided, edit mode; otherwise create mode
  onSuccess?: () => void;
}

interface FormData {
  name: string;
  symbol: string;
  description: string;
  provider: Provider | null;
  provider_symbol: string;
}

const PROVIDER_OPTIONS = [
  { value: '', label: 'None' },
  { value: 'yahoo', label: 'Yahoo Finance' },
  { value: 'cal', label: 'CAL' },
];

export function UnitTrustFormModal({
  isOpen,
  onClose,
  unitTrust,
  onSuccess,
}: UnitTrustFormModalProps) {
  const isEditMode = !!unitTrust;
  const createMutation = useCreateUnitTrust();
  const updateMutation = useUpdateUnitTrust();

  const [formData, setFormData] = useState<FormData>({
    name: '',
    symbol: '',
    description: '',
    provider: null,
    provider_symbol: '',
  });

  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});

  // Initialize form with unit trust data in edit mode
  useEffect(() => {
    if (unitTrust) {
      setFormData({
        name: unitTrust.name,
        symbol: unitTrust.symbol,
        description: unitTrust.description || '',
        provider: unitTrust.provider,
        provider_symbol: unitTrust.provider_symbol || '',
      });
    } else {
      setFormData({
        name: '',
        symbol: '',
        description: '',
        provider: null,
        provider_symbol: '',
      });
    }
    setErrors({});
  }, [unitTrust, isOpen]);

  const handleChange = (field: keyof FormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const handleProviderChange = (value: string) => {
    const provider = value === '' ? null : (value as Provider);
    setFormData((prev) => ({ ...prev, provider }));
    if (errors.provider) {
      setErrors((prev) => ({ ...prev, provider: undefined }));
    }
  };

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof FormData, string>> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.symbol.trim()) {
      newErrors.symbol = 'Symbol is required';
    } else if (!/^[A-Z0-9.-]+$/i.test(formData.symbol)) {
      newErrors.symbol = 'Symbol should only contain letters, numbers, dots, and hyphens';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    try {
      if (isEditMode && unitTrust) {
        // Update mode
        const updateData: UnitTrustUpdate = {
          name: formData.name.trim(),
          symbol: formData.symbol.trim().toUpperCase(),
          description: formData.description.trim() || undefined,
          provider: formData.provider || undefined,
          provider_symbol: formData.provider_symbol.trim() || undefined,
        };

        await updateMutation.mutateAsync({ id: unitTrust.id, data: updateData });
      } else {
        // Create mode
        const createData: UnitTrustCreate = {
          name: formData.name.trim(),
          symbol: formData.symbol.trim().toUpperCase(),
          description: formData.description.trim() || undefined,
          provider: formData.provider || undefined,
          provider_symbol: formData.provider_symbol.trim() || undefined,
        };

        await createMutation.mutateAsync(createData);
      }

      onSuccess?.();
      onClose();
    } catch (error) {
      console.error('Failed to save unit trust:', error);
      // Error handling can be enhanced with toast notifications
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditMode ? 'Edit Fund' : 'Add New Fund'}
      description={
        isEditMode
          ? 'Update the fund details and provider configuration'
          : 'Create a new unit trust fund with optional price provider'
      }
      size="lg"
    >
      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.grid}>
          {/* Name */}
          <div className={styles.fullWidth}>
            <Input
              label="Fund Name"
              placeholder="e.g., Apple Inc"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              error={errors.name}
              disabled={isPending}
              required
            />
          </div>

          {/* Symbol */}
          <Input
            label="Symbol"
            placeholder="e.g., AAPL"
            value={formData.symbol}
            onChange={(e) => handleChange('symbol', e.target.value)}
            error={errors.symbol}
            disabled={isPending}
            required
          />

          {/* Provider */}
          <div className={styles.providerField}>
            <Select
              label="Price Provider"
              options={PROVIDER_OPTIONS}
              value={formData.provider || ''}
              onChange={(e) => handleProviderChange(e.target.value)}
              error={errors.provider}
              disabled={isPending}
              hint="Automatically fetch prices from external sources"
            />
            {formData.provider && (
              <div className={styles.providerPreview}>
                <ProviderBadge provider={formData.provider} showIcon />
              </div>
            )}
          </div>

          {/* Provider Symbol - conditional */}
          <AnimatePresence mode="wait">
            {formData.provider && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2 }}
                className={styles.providerSymbolField}
              >
                <Input
                  label="Provider Symbol"
                  placeholder="Leave blank to use main symbol"
                  value={formData.provider_symbol}
                  onChange={(e) => handleChange('provider_symbol', e.target.value)}
                  error={errors.provider_symbol}
                  disabled={isPending}
                  hint={
                    formData.provider === 'yahoo'
                      ? 'Yahoo Finance ticker (e.g., AAPL, MSFT)'
                      : 'CAL symbol for price lookup'
                  }
                />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Description */}
          <div className={styles.fullWidth}>
            <Textarea
              label="Description"
              placeholder="Optional description or notes about this fund"
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              error={errors.description}
              disabled={isPending}
              rows={3}
            />
          </div>
        </div>

        <ModalFooter>
          <Button variant="ghost" onClick={onClose} disabled={isPending} type="button">
            Cancel
          </Button>
          <Button type="submit" loading={isPending}>
            {isEditMode ? 'Save Changes' : 'Create Fund'}
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  );
}
