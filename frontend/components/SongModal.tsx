'use client';

import { useEffect } from 'react';

interface SongResult {
    title: string;
    artist: string;
    fingerprint: string;
    duration: number;
    lyrics: string;
    classification: string;
    accuracy: number;
}

interface Props {
    isOpen: boolean;
    onClose: () => void;
    result: SongResult | null;
}

export default function SongModal({ isOpen, onClose, result }: Props) {
    useEffect(() => {
        const handleEsc = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
        };
        document.addEventListener('keydown', handleEsc);
        return () => document.removeEventListener('keydown', handleEsc);
    }, [onClose]);

    if (!isOpen || !result) return null;

    return (
        <div className="fixed inset-0 z-50 bg-black/5 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-white/100 text-black rounded-lg shadow-lg w-full max-w-2xl max-h-[80vh] overflow-y-auto p-5 relative border border-white/20 backdrop-blur-md">
                <button
                    onClick={onClose}
                    className="absolute top-3 right-3 text-black text-2xl hover:opacity-70"
                >
                    &times;
                </button>

                <h2 className="text-xl font-bold mb-1">{result.title}</h2>
                <p className="text-md text-gray-800 mb-3">by {result.artist}</p>

                <div className="grid grid-cols-2 gap-3 mb-3 text-sm">
                    <div>
                        <span className="text-gray-600 font-semibold">Duration:</span>
                        <p>{result.duration} sec</p>
                    </div>
                    <div>
                        <span className="text-gray-600 font-semibold">Classification:</span>
                        <p>{result.classification} ({(result.accuracy * 100).toFixed(2)}%)</p>
                    </div>
                    <div className="col-span-2">
                        <span className="text-gray-600 font-semibold">Lyrics:</span>
                        <pre className="whitespace-pre-wrap bg-white/50 rounded p-3 text-sm text-gray-900">
                            {result.lyrics}
                        </pre>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-3 mb-3 text-sm">
                    <div className="col-span-2">
                        <span className="text-gray-600 font-semibold">Fingerprint:</span>
                        <pre className="whitespace-pre-wrap break-words overflow-x-hidden bg-white/50 rounded p-3 text-sm text-gray-900 max-h-[200px] overflow-y-auto">
                            {result.fingerprint}
                        </pre>

                    </div>
                </div>
            </div>
        </div>
    );
}
