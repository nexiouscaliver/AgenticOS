"use client";

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone'; // Need to install this
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Upload, File, CheckCircle, AlertCircle } from 'lucide-react';
import { uploadDocument } from '@/lib/api';
import { toast } from "sonner";

export function DocumentUploader() {
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);

    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        setUploading(true);
        setProgress(0);

        for (const file of acceptedFiles) {
            try {
                setProgress(10);
                await uploadDocument(file);
                setProgress(100);
                toast.success(`Successfully uploaded ${file.name}`);
            } catch (error) {
                console.error(error);
                toast.error(`Failed to upload ${file.name}`);
            }
        }

        setUploading(false);
        setProgress(0);
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

    return (
        <Card className="w-full">
            <CardHeader>
                <CardTitle>Upload Documents</CardTitle>
            </CardHeader>
            <CardContent>
                <div
                    {...getRootProps()}
                    className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors ${isDragActive ? 'border-primary bg-primary/10' : 'border-muted-foreground/25'
                        }`}
                >
                    <input {...getInputProps()} />
                    <div className="flex flex-col items-center justify-center gap-4">
                        <div className="p-4 bg-background rounded-full shadow-sm">
                            <Upload className="h-8 w-8 text-muted-foreground" />
                        </div>
                        <div className="space-y-1">
                            <p className="text-sm font-medium">
                                Drag & drop files here, or click to select
                            </p>
                            <p className="text-xs text-muted-foreground">
                                PDF, Images, CSV, Excel, JSON (Max 50MB)
                            </p>
                        </div>
                    </div>
                </div>

                {uploading && (
                    <div className="mt-4 space-y-2">
                        <div className="flex justify-between text-xs">
                            <span>Uploading...</span>
                            <span>{progress}%</span>
                        </div>
                        <Progress value={progress} />
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
