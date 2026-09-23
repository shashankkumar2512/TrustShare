import React from 'react';
import { User, Building, Crown, Shield, Calendar } from 'lucide-react';

const InfoRow = ({ icon, label, value, highlight, capitalize }) => (
    <div className="asst-profile-info-row">
        <span className="asst-profile-info-icon">{icon}</span>
        <span className="asst-profile-info-label">{label}</span>
        <span
            className={`asst-profile-info-value ${highlight ? 'highlight' : ''} ${capitalize ? 'capitalize' : ''}`}
        >
            {value}
        </span>
    </div>
);

const ProfileCard = ({ result }) => {
    if (!result) return null;

    const initials = result.name
        ?.split(' ')
        .map((w) => w[0])
        .slice(0, 2)
        .join('')
        .toUpperCase() || 'U';

    return (
        <div className="asst-card">
            <div className="asst-card-body">
                {/* Avatar + Name */}
                <div className="asst-profile-header">
                    <div className="asst-profile-avatar">{initials}</div>
                    <div>
                        <div className="asst-profile-name">{result.name}</div>
                        <div className="asst-profile-email">{result.email}</div>
                    </div>
                </div>

                {/* Info rows */}
                <div className="asst-profile-info-list">
                    <InfoRow
                        icon={<Building size={14} />}
                        label="Organization"
                        value={result.organization || '—'}
                    />
                    <InfoRow
                        icon={<Crown size={14} />}
                        label="Plan"
                        value={result.plan}
                        capitalize
                    />
                    <InfoRow
                        icon={<User size={14} />}
                        label="Role"
                        value={result.role}
                        capitalize
                    />
                    <InfoRow
                        icon={<Shield size={14} />}
                        label="MFA"
                        value={result.mfa_enabled ? 'Enabled' : 'Disabled'}
                        highlight={result.mfa_enabled}
                    />
                    <InfoRow
                        icon={<Calendar size={14} />}
                        label="Member Since"
                        value={result.member_since}
                    />
                </div>
            </div>
        </div>
    );
};

export default ProfileCard;