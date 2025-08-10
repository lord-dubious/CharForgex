const { createApp } = Vue;

createApp({
    data() {
        return {
            // UI State
            activeTab: 'inference',
            loading: false,
            workerStatus: 'offline',
            statusMessage: null,
            
            // Configuration
            endpointUrl: localStorage.getItem('endpointUrl') || '',
            apiKey: localStorage.getItem('apiKey') || '',
        useLocalAPI: localStorage.getItem('useLocalAPI') === 'true' || false,
            
            // Tabs
            tabs: [
                { id: 'inference', name: 'Generate Images' },
                { id: 'training', name: 'Train Character' },
                { id: 'characters', name: 'Characters' }
            ],
            
            // Training data
            training: {
                characterName: '',
                imageFile: null,
                imagePreview: null,
                steps: 800,
                learningRate: '8e-4',
                rankDim: 8
            },
            
            // Inference data
            inference: {
                characterName: '',
                prompt: '',
                loraWeight: 0.73,
                imageSize: 1024,
                steps: 30,
                batchSize: 1
            },
            
            // Data
            availableCharacters: [],
            generatedImages: []
        };
    },
    
    computed: {
        canStartTraining() {
            return this.training.characterName && this.training.imageFile && this.endpointUrl && this.apiKey;
        },
        
        canGenerate() {
            return this.inference.characterName && this.inference.prompt && this.endpointUrl && this.apiKey;
        }
    },
    
    mounted() {
        this.loadCharacters();
        if (this.endpointUrl && this.apiKey) {
            this.testConnection();
        }
    },
    
    watch: {
        endpointUrl(newVal) {
            localStorage.setItem('endpointUrl', newVal);
        },
        apiKey(newVal) {
            localStorage.setItem('apiKey', newVal);
        }
    },
    
    methods: {
        async makeRequest(operation, data) {
            if (this.useLocalAPI) {
                // Use local API endpoints
                let endpoint;
                switch (operation) {
                    case 'inference':
                    case 'generate':
                        endpoint = '/api/inference';
                        break;
                    case 'training':
                    case 'train':
                        endpoint = '/api/training';
                        break;
                    case 'list_characters':
                    case 'list':
                        endpoint = '/api/characters';
                        return await axios.get(endpoint);
                    case 'health_check':
                    case 'system_status':
                        endpoint = '/health';
                        return await axios.get(endpoint);
                    default:
                        throw new Error(`Unsupported operation for local API: ${operation}`);
                }

                const response = await axios.post(endpoint, data, {
                    timeout: 300000 // 5 minutes timeout
                });

                return response.data;
            } else {
                // Use RunPod endpoint
                if (!this.endpointUrl || !this.apiKey) {
                    throw new Error('Endpoint URL and API Key are required for RunPod');
                }

                const response = await axios.post(this.endpointUrl, {
                    input: {
                        operation: operation,
                        ...data
                    }
                }, {
                    headers: {
                        'Authorization': `Bearer ${this.apiKey}`,
                        'Content-Type': 'application/json'
                    },
                    timeout: 300000 // 5 minutes timeout
                });

                return response.data;
            }
        },
        
        async testConnection() {
            this.loading = true;
            try {
                const result = await this.makeRequest('system_status', {});
                if (result.status === 'healthy') {
                    this.workerStatus = 'online';
                    this.showMessage(`Connection successful! GPU: ${result.gpu_info?.gpu_name || 'Unknown'}`, 'success');

                    // Display system info
                    if (result.storage_info) {
                        const storage = result.storage_info;
                        console.log(`Storage: ${storage.used_gb}GB / ${storage.total_gb}GB used (${storage.usage_percent}%)`);
                    }

                    // Auto-load characters if connection successful
                    this.loadCharacters();
                } else {
                    this.workerStatus = 'offline';
                    this.showMessage('Worker is not responding properly', 'error');
                }
            } catch (error) {
                this.workerStatus = 'offline';
                let errorMsg = 'Connection failed';

                if (error.response?.status === 401) {
                    errorMsg = 'Invalid API key';
                } else if (error.response?.status === 404) {
                    errorMsg = 'Endpoint not found - check your endpoint URL';
                } else if (error.code === 'ECONNABORTED') {
                    errorMsg = 'Connection timeout - worker may be starting up';
                } else {
                    errorMsg = `Connection failed: ${error.message}`;
                }

                this.showMessage(errorMsg, 'error');
            } finally {
                this.loading = false;
            }
        },
        
        async loadCharacters() {
            try {
                if (!this.endpointUrl || !this.apiKey) return;
                
                const result = await this.makeRequest('list_characters', {});
                if (result.status === 'completed') {
                    this.availableCharacters = result.characters.map(c => c.name);
                }
            } catch (error) {
                console.error('Failed to load characters:', error);
            }
        },
        
        handleImageUpload(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            this.training.imageFile = file;
            
            // Create preview
            const reader = new FileReader();
            reader.onload = (e) => {
                this.training.imagePreview = e.target.result;
            };
            reader.readAsDataURL(file);
        },
        
        clearImage() {
            this.training.imageFile = null;
            this.training.imagePreview = null;
            this.$refs.imageInput.value = '';
        },
        
        async startTraining() {
            if (!this.canStartTraining) return;

            this.loading = true;
            let jobId = null;

            try {
                // Validate inputs
                if (this.training.characterName.length < 2) {
                    throw new Error('Character name must be at least 2 characters long');
                }

                if (!this.training.imageFile.type.startsWith('image/')) {
                    throw new Error('Please upload a valid image file');
                }

                // Check file size (max 10MB)
                if (this.training.imageFile.size > 10 * 1024 * 1024) {
                    throw new Error('Image file must be smaller than 10MB');
                }

                // Convert image to base64
                this.showMessage('Preparing image...', 'info');
                const imageBase64 = await this.fileToBase64(this.training.imageFile);

                const trainingData = {
                    character_name: this.training.characterName.trim(),
                    input_image: imageBase64,
                    steps: this.training.steps,
                    learning_rate: parseFloat(this.training.learningRate),
                    rank_dim: this.training.rankDim
                };

                this.showMessage('Starting training... This may take 30-40 minutes.', 'info');

                // Use async endpoint for training (long-running operation)
                const asyncUrl = this.endpointUrl.replace('/runsync', '/run');
                const response = await axios.post(asyncUrl, {
                    input: {
                        operation: 'training',
                        ...trainingData
                    }
                }, {
                    headers: {
                        'Authorization': `Bearer ${this.apiKey}`,
                        'Content-Type': 'application/json'
                    }
                });

                jobId = response.data.id;
                this.showMessage(`Training job started (ID: ${jobId}). Monitoring progress...`, 'info');

                // Poll for completion
                const result = await this.pollJobCompletion(jobId);

                if (result.status === 'COMPLETED' && result.output?.status === 'completed') {
                    const trainingTime = result.output.training_time_seconds || 0;
                    this.showMessage(
                        `Training completed for ${this.training.characterName} in ${Math.round(trainingTime/60)} minutes!`,
                        'success'
                    );
                    this.loadCharacters(); // Refresh character list
                    this.clearTrainingForm();
                } else {
                    const error = result.output?.error || result.error || 'Training failed';
                    throw new Error(error);
                }

            } catch (error) {
                let errorMessage = 'Training failed';

                if (error.response?.status === 413) {
                    errorMessage = 'Image file too large. Please use a smaller image.';
                } else if (error.response?.status === 429) {
                    errorMessage = 'Rate limit exceeded. Please wait before trying again.';
                } else if (error.message.includes('timeout')) {
                    errorMessage = 'Training timed out. This may happen with very large models.';
                } else {
                    errorMessage = `Training failed: ${error.message}`;
                }

                this.showMessage(errorMessage, 'error');
                console.error('Training error:', error);

                // If we have a job ID, try to get more details
                if (jobId) {
                    try {
                        const jobStatus = await this.getJobStatus(jobId);
                        console.error('Job details:', jobStatus);
                    } catch (statusError) {
                        console.error('Failed to get job status:', statusError);
                    }
                }
            } finally {
                this.loading = false;
            }
        },
        
        async generateImages() {
            if (!this.canGenerate) return;
            
            this.loading = true;
            this.generatedImages = [];
            
            try {
                const inferenceData = {
                    character_name: this.inference.characterName,
                    prompt: this.inference.prompt,
                    lora_weight: this.inference.loraWeight,
                    test_dim: this.inference.imageSize,
                    num_inference_steps: this.inference.steps,
                    batch_size: this.inference.batchSize
                };
                
                this.showMessage('Generating images...', 'info');
                
                const result = await this.makeRequest('inference', inferenceData);
                
                if (result.status === 'completed') {
                    this.generatedImages = result.images;
                    this.showMessage(`Generated ${result.num_images} images successfully!`, 'success');
                } else {
                    throw new Error(result.error || 'Image generation failed');
                }
                
            } catch (error) {
                this.showMessage(`Generation failed: ${error.message}`, 'error');
                console.error('Generation error:', error);
            } finally {
                this.loading = false;
            }
        },
        
        selectCharacterForInference(characterName) {
            this.inference.characterName = characterName;
            this.activeTab = 'inference';
            this.showMessage(`Selected ${characterName} for inference`, 'success');
        },
        
        downloadImage(image, index) {
            const link = document.createElement('a');
            link.href = `data:image/jpeg;base64,${image.image_data}`;
            link.download = image.filename || `generated_image_${index + 1}.jpg`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        },
        
        clearTrainingForm() {
            this.training.characterName = '';
            this.clearImage();
            this.training.steps = 800;
            this.training.learningRate = '8e-4';
            this.training.rankDim = 8;
        },
        
        fileToBase64(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => {
                    // Remove data URL prefix
                    const base64 = reader.result.split(',')[1];
                    resolve(base64);
                };
                reader.onerror = reject;
                reader.readAsDataURL(file);
            });
        },
        
        async pollJobCompletion(jobId, maxWaitMinutes = 60) {
            const statusUrl = this.endpointUrl.replace('/runsync', '/status/').replace('/run', '/status/') + jobId;
            const maxAttempts = maxWaitMinutes * 2; // Check every 30 seconds

            for (let attempt = 0; attempt < maxAttempts; attempt++) {
                try {
                    const response = await axios.get(statusUrl, {
                        headers: {
                            'Authorization': `Bearer ${this.apiKey}`
                        }
                    });

                    const status = response.data.status;

                    if (status === 'COMPLETED' || status === 'FAILED') {
                        return response.data;
                    }

                    // Update progress message
                    const elapsed = Math.round((attempt + 1) * 0.5);
                    this.showMessage(`Training in progress... ${elapsed} minutes elapsed`, 'info');

                    // Wait 30 seconds before next check
                    await new Promise(resolve => setTimeout(resolve, 30000));

                } catch (error) {
                    if (attempt === maxAttempts - 1) {
                        throw error;
                    }
                    // Wait before retry
                    await new Promise(resolve => setTimeout(resolve, 5000));
                }
            }

            throw new Error('Training timed out after ' + maxWaitMinutes + ' minutes');
        },

        async getJobStatus(jobId) {
            const statusUrl = this.endpointUrl.replace('/runsync', '/status/').replace('/run', '/status/') + jobId;
            const response = await axios.get(statusUrl, {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`
                }
            });
            return response.data;
        },

        showMessage(text, type = 'info') {
            this.statusMessage = { text, type };

            // Auto-dismiss after different times based on type
            const dismissTime = type === 'error' ? 10000 : type === 'success' ? 7000 : 5000;

            setTimeout(() => {
                if (this.statusMessage && this.statusMessage.text === text) {
                    this.statusMessage = null;
                }
            }, dismissTime);
        }
    }
}).mount('#app');
