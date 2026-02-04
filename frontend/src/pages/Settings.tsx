import { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { PageHeader } from '../components/layout';
import { Card, Button, Input } from '../components/ui';
import { useNotificationSettings, useUpdateNotificationSettings } from '../api/hooks';
import styles from './Settings.module.css';

export function Settings() {
  const { data: settings, isLoading } = useNotificationSettings();
  const updateMutation = useUpdateNotificationSettings();

  const [formData, setFormData] = useState({
    notify_days_before_30: true,
    notify_days_before_7: true,
    notify_on_maturity: true,
    email_notifications_enabled: false,
    email_address: '',
  });

  const [hasChanges, setHasChanges] = useState(false);

  // Initialize form with settings
  useEffect(() => {
    if (settings) {
      setFormData({
        notify_days_before_30: settings.notify_days_before_30,
        notify_days_before_7: settings.notify_days_before_7,
        notify_on_maturity: settings.notify_on_maturity,
        email_notifications_enabled: settings.email_notifications_enabled,
        email_address: settings.email_address || '',
      });
      setHasChanges(false);
    }
  }, [settings]);

  const handleCheckboxChange = (field: keyof typeof formData, value: boolean) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setHasChanges(true);
  };

  const handleInputChange = (field: keyof typeof formData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setHasChanges(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await updateMutation.mutateAsync(formData);
      setHasChanges(false);
    } catch (error) {
      console.error('Failed to update settings:', error);
    }
  };

  const handleReset = () => {
    if (settings) {
      setFormData({
        notify_days_before_30: settings.notify_days_before_30,
        notify_days_before_7: settings.notify_days_before_7,
        notify_on_maturity: settings.notify_on_maturity,
        email_notifications_enabled: settings.email_notifications_enabled,
        email_address: settings.email_address || '',
      });
      setHasChanges(false);
    }
  };

  return (
    <div className={styles.page}>
      <PageHeader
        title="Settings"
        description="Configure your notification preferences and application settings"
      />

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={styles.content}
      >
        <Card>
          <form onSubmit={handleSubmit} className={styles.form}>
            {/* FD Maturity Notifications Section */}
            <div className={styles.section}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>FD Maturity Notifications</h2>
                <p className={styles.sectionDescription}>
                  Get notified when your fixed deposits are approaching maturity
                </p>
              </div>

              <div className={styles.settingsGroup}>
                <label className={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    checked={formData.notify_days_before_30}
                    onChange={(e) =>
                      handleCheckboxChange('notify_days_before_30', e.target.checked)
                    }
                    disabled={isLoading || updateMutation.isPending}
                    className={styles.checkbox}
                  />
                  <div className={styles.checkboxContent}>
                    <span className={styles.checkboxTitle}>30 Days Before Maturity</span>
                    <span className={styles.checkboxDescription}>
                      Get notified one month before your FD matures
                    </span>
                  </div>
                </label>

                <label className={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    checked={formData.notify_days_before_7}
                    onChange={(e) =>
                      handleCheckboxChange('notify_days_before_7', e.target.checked)
                    }
                    disabled={isLoading || updateMutation.isPending}
                    className={styles.checkbox}
                  />
                  <div className={styles.checkboxContent}>
                    <span className={styles.checkboxTitle}>7 Days Before Maturity</span>
                    <span className={styles.checkboxDescription}>
                      Get notified one week before your FD matures
                    </span>
                  </div>
                </label>

                <label className={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    checked={formData.notify_on_maturity}
                    onChange={(e) =>
                      handleCheckboxChange('notify_on_maturity', e.target.checked)
                    }
                    disabled={isLoading || updateMutation.isPending}
                    className={styles.checkbox}
                  />
                  <div className={styles.checkboxContent}>
                    <span className={styles.checkboxTitle}>On Maturity Date</span>
                    <span className={styles.checkboxDescription}>
                      Get notified on the day your FD matures
                    </span>
                  </div>
                </label>
              </div>
            </div>

            {/* Email Notifications Section */}
            <div className={styles.section}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>Email Notifications</h2>
                <p className={styles.sectionDescription}>
                  Receive notifications via email (coming soon)
                </p>
              </div>

              <div className={styles.settingsGroup}>
                <label className={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    checked={formData.email_notifications_enabled}
                    onChange={(e) =>
                      handleCheckboxChange('email_notifications_enabled', e.target.checked)
                    }
                    disabled
                    className={styles.checkbox}
                  />
                  <div className={styles.checkboxContent}>
                    <span className={styles.checkboxTitle}>Enable Email Notifications</span>
                    <span className={styles.checkboxDescription}>
                      This feature is coming soon
                    </span>
                  </div>
                </label>

                <Input
                  label="Email Address"
                  type="email"
                  placeholder="your@email.com"
                  value={formData.email_address}
                  onChange={(e) => handleInputChange('email_address', e.target.value)}
                  disabled
                  hint="Email notifications are not yet available"
                />
              </div>
            </div>

            {/* Form Actions */}
            <div className={styles.formActions}>
              <Button
                type="button"
                variant="ghost"
                onClick={handleReset}
                disabled={!hasChanges || updateMutation.isPending}
              >
                Reset
              </Button>
              <Button
                type="submit"
                loading={updateMutation.isPending}
                disabled={!hasChanges || isLoading}
              >
                Save Changes
              </Button>
            </div>
          </form>
        </Card>
      </motion.div>
    </div>
  );
}
